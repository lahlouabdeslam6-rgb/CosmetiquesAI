import json
import secrets
from datetime import UTC, date, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_roles
from app.db.sqlite import get_sqlite_session
from app.db.sqlite import SqliteSession
from app.models.cosmetic_formulation import CosmeticRequest, RawMaterial
from app.models.operations import AuditLog, Notification
from app.models.site_setting import SiteSetting
from app.models.user import User
from app.schemas.product import ProductCreate
from app.schemas.product_media import ProductMediaPrepareRequest
from app.services.cosmetic_questionnaire import DEFAULT_QUESTIONNAIRE, PRODUCT_TYPES, QUESTION_LABELS
from app.services.product import ProductService
from app.services.raw_material_catalog import catalog_metadata, load_catalog
from app.services.product_media_agent import ProductMediaAgentService, run_local_product_media_generation
from app.services.laboratory_agent import (
    LaboratoryAgentService,
    build_local_manufacturing_plan,
)
from app.services.formulation_documents import build_formulation_document

router = APIRouter(tags=["Formulation cosmétique"])
ACTIVE_PROCEDURE_JOBS: set[str] = set()


class MaterialWrite(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    reference: str | None = Field(default=None, max_length=80)
    unit: str = Field(default="g", min_length=1, max_length=20)
    quantity: float = Field(default=0, ge=0)
    reserved_quantity: float = Field(default=0, ge=0)
    minimum_quantity: float = Field(default=0, ge=0)
    cost_per_unit: float | None = Field(default=None, ge=0)
    supplier: str | None = Field(default=None, max_length=180)
    expires_on: date | None = None
    is_active: bool = True

    @field_validator("name", "unit")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ce champ est obligatoire")
        return value


class MaterialPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    reference: str | None = Field(default=None, max_length=80)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    quantity: float | None = Field(default=None, ge=0)
    reserved_quantity: float | None = Field(default=None, ge=0)
    minimum_quantity: float | None = Field(default=None, ge=0)
    cost_per_unit: float | None = Field(default=None, ge=0)
    supplier: str | None = Field(default=None, max_length=180)
    expires_on: date | None = None
    is_active: bool | None = None


AnswerValue = str | int | float | bool | list[str] | None


class CosmeticRequestWrite(BaseModel):
    project_name: str | None = Field(default=None, max_length=180)
    phone: str = Field(min_length=6, max_length=40)
    product_type: str = Field(min_length=1, max_length=120)
    needs: str = Field(default="", max_length=5000)
    answers: dict[str, AnswerValue] = Field(default_factory=dict)


class MaterialDecisionWrite(BaseModel):
    can_source: bool
    note: str | None = Field(default=None, max_length=2000)


class FormulaFeedbackWrite(BaseModel):
    feedback: str = Field(min_length=3, max_length=3000)


class FormulaGenerateWrite(BaseModel):
    count: int = Field(default=1, ge=1, le=5)


class FormulaSelectWrite(BaseModel):
    formula_index: int = Field(ge=0)


class FormulaConversationWrite(BaseModel):
    message: str = Field(min_length=2, max_length=3000)
    formula_index: int = Field(default=0, ge=0)


class FormulaApprovalWrite(BaseModel):
    product_name: str = Field(min_length=2, max_length=240)
    price: float = Field(default=0, ge=0)
    category: str | None = Field(default="Cosmétique", max_length=120)
    media_mode: Literal["agent", "upload", "later"] = "agent"
    visual_style: str = Field(default="premium naturel", min_length=3, max_length=120)
    image_description: str | None = Field(default=None, max_length=1500)
    video_description: str | None = Field(default=None, max_length=1500)


def _json(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value) if value else fallback
    except (TypeError, ValueError):
        return fallback


def material_dict(row: RawMaterial) -> dict[str, Any]:
    available = max(0.0, row.quantity - row.reserved_quantity)
    catalog = catalog_metadata(row)
    return {
        "id": row.id, "name": row.name, "reference": row.reference,
        "catalog": catalog,
        "unit": row.unit, "quantity": row.quantity,
        "reserved_quantity": row.reserved_quantity, "available_quantity": available,
        "minimum_quantity": row.minimum_quantity, "cost_per_unit": row.cost_per_unit,
        "supplier": row.supplier, "expires_on": row.expires_on,
        "is_active": row.is_active,
        "stock_status": "unrecorded" if catalog.get("stock_recorded") is False else "low" if available <= row.minimum_quantity else "healthy",
        "created_at": row.created_at, "updated_at": row.updated_at,
    }


def request_dict(row: CosmeticRequest) -> dict[str, Any]:
    answers = _json(row.answers_json, {})
    return {
        "id": row.id, "reference": row.reference, "user_id": row.user_id,
        "project_name": row.project_name, "client_name": row.client_name,
        "email": row.email, "phone": row.phone, "product_type": row.product_type,
        "needs": row.needs, "answers": answers,
        "answer_details": [{"id": key, "label": QUESTION_LABELS.get(key, key), "value": value} for key, value in answers.items()],
        "client_snapshot": _json(row.client_snapshot_json, {}),
        "status": row.status, "formula": _json(row.formula_json, None),
        "formulas": _json(row.formulas_json, []),
        "conversation": _json(row.conversation_json, []),
        "selected_formula_index": row.selected_formula_index,
        "lab_report": _json(row.lab_report_json, None),
        "missing_materials": _json(row.missing_materials_json, []),
        "material_decision": _json(row.material_decision_json, {}),
        "ai_note": row.ai_note, "admin_feedback": row.admin_feedback,
        "revision": row.revision, "product_id": row.product_id,
        "approved_by": row.approved_by, "approved_at": row.approved_at,
        "created_at": row.created_at, "updated_at": row.updated_at,
    }


def audit(session: AsyncSession, user: User, action: str, entity: str, entity_id: int, details: dict[str, Any]) -> None:
    session.add(AuditLog(actor_id=user.id, actor_role=user.role, action=action, entity_type=entity, entity_id=str(entity_id), details=json.dumps(details, ensure_ascii=False)))


def _number(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _suggested_tests(answers: dict[str, Any]) -> dict[str, list[str]]:
    requested = answers.get("tests") or []
    if isinstance(requested, str):
        requested = [requested]
    stability = ["Stabilité accélérée et à température ambiante", "Cycles chaud/froid", "Compatibilité contenu/contenant", "Suivi du pH, viscosité, couleur, odeur et aspect"]
    efficacy = [str(item) for item in requested if str(item) not in {"Stabilité", "Compatibilité contenu / contenant", "Challenge test"}]
    if not efficacy:
        efficacy = ["Test d’usage sur la cible définie dans le cahier des charges"]
    if "Challenge test" in requested:
        stability.append("Challenge test du système conservateur")
    return {"stability": stability, "efficacy": efficacy}


def _build_formula_variant(
    proposal: dict[str, Any],
    *,
    request: CosmeticRequest,
    materials: list[RawMaterial],
    answers: dict[str, Any],
    approved_history: list[dict[str, Any]],
    version: int,
) -> dict[str, Any]:
    batch_size_g = float(proposal["batch_size_g"])
    by_id = {material.id: material for material in materials}
    ingredients: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for ingredient in proposal["ingredients"]:
        material = by_id.get(ingredient.get("material_id"))
        required = round(batch_size_g * float(ingredient["percentage"]) / 100, 4)
        available = max(0.0, material.quantity - material.reserved_quantity) if material else 0.0
        item = {**ingredient, "required_quantity": required, "unit": material.unit if material else "g"}
        ingredients.append(item)
        if not material or available < required:
            missing.append({
                **item,
                "available": round(available, 4),
                "missing": round(max(0, required - available), 4),
                "supplier": material.supplier if material else None,
                "purchase_proposal": material is None,
                "validated_alternatives": [],
            })
    total = round(sum(float(item["percentage"]) for item in ingredients), 4)
    tests = _suggested_tests(answers)
    consistency = [f"{item['name']} — {item['role']}" for item in ingredients if any(term in (item["role"] + " " + item["name"]).lower() for term in ("texture", "consistance", "gél", "émuls"))]
    repair = [f"{item['name']} — {item['role']}" for item in ingredients if any(term in (item["role"] + " " + item["name"]).lower() for term in ("hydrat", "répar", "actif", "apais"))]
    formula = {
        "product_type": request.product_type,
        "suggested_name": proposal["suggested_name"],
        "batch_size_g": batch_size_g,
        "total_percentage": total,
        "ingredients": ingredients,
        "source": "laboratory_agent",
    }
    report = {
        "summary": proposal["product_concept"],
        "suggested_name": proposal["suggested_name"],
        "ingredient_justifications": [{"name": item["name"], "percentage": item["percentage"], "role": item["role"], "reason": item["justification"]} for item in ingredients],
        "consistency_and_additives": proposal["consistency_and_additives"] or consistency,
        "hydrating_and_repair_actives": proposal["hydrating_and_repair_actives"] or repair,
        "manufacturing_process": proposal["manufacturing_process"],
        "manufacturing_steps": proposal.get("manufacturing_steps", []),
        "process_parameters_to_confirm": proposal.get("process_parameters_to_confirm", []),
        "process_status": proposal.get("process_status", "not_detailed"),
        "stability_tests": list(dict.fromkeys([*proposal["stability_tests"], *tests["stability"]])),
        "efficacy_tests": list(dict.fromkeys([*proposal["efficacy_tests"], *tests["efficacy"]])),
        "packaging": answers.get("packaging_type") or [],
        "markets": answers.get("markets") or [],
        "validation_memory": {"approved_formulas": len(approved_history), "latest_admin_feedback": [item.get("admin_feedback") for item in approved_history[-3:] if item.get("admin_feedback")]},
        "warnings": list(dict.fromkeys([*proposal["warnings"], "Proposition à valider par un formulateur qualifié et par l'administrateur avant fabrication ou commercialisation."])),
    }
    return {
        "version": version,
        "formula": formula,
        "lab_report": report,
        "missing_materials": missing,
        "status": "needs_materials" if missing else "draft_ready",
        "created_at": datetime.now(UTC).isoformat(),
    }


@router.get("/cosmetic-requests/config")
async def public_formulation_config(session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row = await session.get(SiteSetting, "cosmetic_questionnaire")
    configured = (row.value or {}).get("questions") if row else None
    return {"questions": configured or DEFAULT_QUESTIONNAIRE, "product_types": PRODUCT_TYPES, "configured": bool(configured)}


@router.post("/cosmetic-requests", status_code=status.HTTP_201_CREATED)
async def create_cosmetic_request(
    data: CosmeticRequestWrite,
    customer: Annotated[User, Depends(require_roles("customer"))],
    session: Annotated[AsyncSession, Depends(get_sqlite_session)],
):
    reference = "COS-" + secrets.token_hex(4).upper()
    snapshot = {"user_id": customer.id, "full_name": customer.full_name or customer.email.split("@")[0], "email": customer.email, "phone": data.phone.strip(), "submitted_at": datetime.now(UTC).isoformat()}
    row = CosmeticRequest(
        reference=reference, user_id=customer.id, project_name=(data.project_name or "").strip() or None,
        client_name=snapshot["full_name"], email=customer.email, phone=data.phone.strip(),
        product_type=data.product_type.strip(), needs=data.needs.strip(),
        answers_json=json.dumps(data.answers, ensure_ascii=False),
        client_snapshot_json=json.dumps(snapshot, ensure_ascii=False), status="received",
    )
    session.add(row)
    session.add(Notification(target_role="admin", notification_type="cosmetic_request", title="Nouveau cahier des charges cosmétique", message=f"{row.client_name} a envoyé une demande {row.product_type} ({reference}).", link="/admin?tab=formulation-requests"))
    await session.commit(); await session.refresh(row)
    return {"reference": row.reference, "status": row.status}


@router.get("/cosmetic-requests/mine")
async def my_cosmetic_requests(customer: Annotated[User, Depends(require_roles("customer"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    rows = (await session.scalars(select(CosmeticRequest).where(CosmeticRequest.user_id == customer.id).order_by(CosmeticRequest.created_at.desc()))).all()
    return {"items": [request_dict(row) for row in rows], "total": len(rows)}


@router.get("/admin/raw-materials")
async def list_raw_materials(_: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)], include_inactive: bool = False):
    query = select(RawMaterial).order_by(RawMaterial.name)
    if not include_inactive: query = query.where(RawMaterial.is_active.is_(True))
    rows = (await session.scalars(query)).all()
    items = [material_dict(row) for row in rows]
    return {"items": items, "total": len(rows), "low_stock": sum(item["stock_status"] == "low" for item in items), "unrecorded_stock": sum(item["stock_status"] == "unrecorded" for item in items)}


@router.get("/admin/raw-materials/catalogue")
async def get_raw_material_catalogue(_: Annotated[User, Depends(require_roles("admin"))]):
    catalogue = load_catalog()
    return {key: catalogue[key] for key in ("version", "source_label", "notice", "categories", "product_guides", "essentials", "pdf_product_guides")}


@router.post("/admin/raw-materials", status_code=status.HTTP_201_CREATED)
async def create_raw_material(data: MaterialWrite, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    if await session.scalar(select(RawMaterial.id).where(func.lower(RawMaterial.name) == data.name.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette matière existe déjà")
    row = RawMaterial(**data.model_dump()); session.add(row); await session.flush()
    audit(session, user, "raw_material.created", "raw_material", row.id, {"name": row.name, "quantity": row.quantity, "unit": row.unit})
    await session.commit(); await session.refresh(row)
    return material_dict(row)


@router.patch("/admin/raw-materials/{material_id}")
async def update_raw_material(material_id: int, data: MaterialPatch, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row = await session.get(RawMaterial, material_id)
    if not row: raise HTTPException(status.HTTP_404_NOT_FOUND, "Matière introuvable")
    changes = data.model_dump(exclude_unset=True)
    for field in ("name", "unit", "quantity", "reserved_quantity", "minimum_quantity", "is_active"):
        if field in changes and (changes[field] is None or isinstance(changes[field], str) and not changes[field].strip()):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Valeur obligatoire : {field}")
    if changes.get("reserved_quantity", row.reserved_quantity) > changes.get("quantity", row.quantity):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La quantité réservée dépasse le stock")
    if "quantity" in changes:
        row.catalog_json = json.dumps({**catalog_metadata(row), "stock_recorded": True}, ensure_ascii=False)
    for key, value in changes.items(): setattr(row, key, value.strip() if isinstance(value, str) else value)
    audit(session, user, "raw_material.updated", "raw_material", row.id, changes)
    await session.commit(); await session.refresh(row)
    return material_dict(row)


@router.get("/admin/cosmetic-requests")
async def list_cosmetic_requests(background_tasks: BackgroundTasks, _: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)], request_status: Annotated[str | None, Query(alias="status")] = None):
    query = select(CosmeticRequest).order_by(CosmeticRequest.created_at.desc())
    if request_status: query = query.where(CosmeticRequest.status == request_status)
    rows = (await session.scalars(query)).all()
    for row in rows:
        report = _json(row.lab_report_json, {})
        job_id = str(report.get("process_job_id") or "")
        if (
            report.get("process_status") == "generating"
            and job_id
            and job_id not in ACTIVE_PROCEDURE_JOBS
        ):
            background_tasks.add_task(
                run_manufacturing_procedure,
                row.id,
                row.selected_formula_index,
                job_id,
            )
    return {"items": [request_dict(row) for row in rows], "total": len(rows)}


@router.get("/admin/cosmetic-requests/{request_id}")
async def get_cosmetic_request(request_id: int, _: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row = await session.get(CosmeticRequest, request_id)
    if not row: raise HTTPException(status.HTTP_404_NOT_FOUND, "Demande introuvable")
    return request_dict(row)


@router.post("/admin/cosmetic-requests/{request_id}/materials-decision")
async def decide_missing_materials(request_id: int, data: MaterialDecisionWrite, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row = await session.get(CosmeticRequest, request_id)
    if not row: raise HTTPException(status.HTTP_404_NOT_FOUND, "Demande introuvable")
    missing = _json(row.missing_materials_json, [])
    if row.status == "approved": raise HTTPException(409, "La formule est déjà validée")
    row.material_decision_json = json.dumps({"can_source": data.can_source, "note": data.note, "formula_index": row.selected_formula_index, "revision": row.revision, "decided_by": user.id, "decided_at": datetime.now(UTC).isoformat()}, ensure_ascii=False)
    row.status = "materials_to_source" if data.can_source else "alternative_required"
    row.ai_note = "L’administrateur confirme l’approvisionnement des matières manquantes." if data.can_source else "Les matières ne peuvent pas être approvisionnées. Les règles doivent être adaptées et revalidées avant une nouvelle proposition."
    audit(session, user, "cosmetic_materials.decided", "cosmetic_request", row.id, {"can_source": data.can_source, "missing": len(missing)})
    await session.commit(); await session.refresh(row)
    return request_dict(row)


@router.post("/admin/cosmetic-requests/{request_id}/feedback")
async def save_formula_feedback(request_id: int, data: FormulaFeedbackWrite, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row = await session.get(CosmeticRequest, request_id)
    if not row: raise HTTPException(status.HTTP_404_NOT_FOUND, "Demande introuvable")
    if row.status == "approved": raise HTTPException(409, "Le dossier validé est archivé avec son produit")
    row.admin_feedback = data.feedback.strip(); row.status = "changes_requested"
    audit(session, user, "cosmetic_formula.feedback", "cosmetic_request", row.id, {"feedback": row.admin_feedback})
    await session.commit(); await session.refresh(row)
    return request_dict(row)


@router.post("/admin/cosmetic-requests/{request_id}/generate")
async def generate_formula(request_id: int, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)], data: FormulaGenerateWrite = FormulaGenerateWrite(), background_tasks: BackgroundTasks = None):
    request = await session.get(CosmeticRequest, request_id)
    if not request: raise HTTPException(status.HTTP_404_NOT_FOUND, "Demande introuvable")
    if request.status == "approved": raise HTTPException(409, "La formule validée est archivée avec son produit client")
    answers = _json(request.answers_json, {})
    memory_row = await session.get(SiteSetting, "cosmetic_formula_memory")
    approved_history = list((memory_row.value or {}).get("approved", [])) if memory_row else []
    materials = list((await session.scalars(select(RawMaterial).where(RawMaterial.is_active.is_(True)))).all())
    decision = _json(request.material_decision_json, {})
    variants: list[dict[str, Any]] = []
    brief_variants: list[dict[str, Any]] = []
    service = LaboratoryAgentService()
    for variation_index in range(data.count):
        proposal = await service.generate(
            product_idea=request.product_type,
            needs=request.needs,
            answers=answers,
            materials=materials,
            approved_history=approved_history,
            admin_feedback=request.admin_feedback,
            material_decision=decision,
            variation_index=variation_index,
            previous_suggestions=brief_variants,
        )
        variant = _build_formula_variant(
            proposal,
            request=request,
            materials=materials,
            answers=answers,
            approved_history=approved_history,
            version=request.revision + 1,
        )
        variants.append(variant)
        if background_tasks is not None:
            variant["lab_report"]["process_status"] = "generating"
            variant["lab_report"]["process_job_id"] = secrets.token_hex(12)
        brief_variants.append({
            "suggested_name": proposal["suggested_name"],
            "ingredients": [item["name"] for item in proposal["ingredients"]],
        })
    selected_variant = variants[0]
    request.formulas_json = json.dumps(variants, ensure_ascii=False)
    request.selected_formula_index = 0
    request.formula_json = json.dumps(selected_variant["formula"], ensure_ascii=False)
    request.lab_report_json = json.dumps(selected_variant["lab_report"], ensure_ascii=False)
    request.missing_materials_json = json.dumps(selected_variant["missing_materials"], ensure_ascii=False)
    request.revision += 1
    request.status = selected_variant["status"]
    request.ai_note = f"Le Laboratory Agent a créé {data.count} proposition(s) depuis le cahier des charges, le stock et la mémoire des validations. La décision finale appartient à l'administrateur."
    audit(session, user, "cosmetic_formula.generated", "cosmetic_request", request.id, {"status": request.status, "revision": request.revision, "count": data.count})
    if request.status == "draft_ready":
        session.add(Notification(target_role="admin", notification_type="formula_ready", title=f"Formule prête {request.reference}", message="Laboratory Agent a préparé la formule, les justifications, le procédé et les tests.", link=f"/admin?tab=formulation-requests&request={request.id}"))
    elif request.status == "needs_materials":
        session.add(Notification(target_role="admin", notification_type="raw_materials_missing", title=f"Décision matières {request.reference}", message="Indiquez si les matières manquantes peuvent être approvisionnées.", link=f"/admin?tab=formulation-requests&request={request.id}"))
    await session.commit(); await session.refresh(request)
    if background_tasks is not None:
        for index, variant in enumerate(variants):
            job_id = variant["lab_report"]["process_job_id"]
            background_tasks.add_task(run_manufacturing_procedure, request.id, index, job_id)
    return request_dict(request)


@router.post("/admin/cosmetic-requests/{request_id}/select-formula")
async def select_formula(request_id: int, data: FormulaSelectWrite, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row = await session.get(CosmeticRequest, request_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demande introuvable")
    if row.status == "approved": raise HTTPException(409, "La formule validée ne peut plus être remplacée")
    formulas = _json(row.formulas_json, [])
    if data.formula_index >= len(formulas):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Formule introuvable")
    variant = formulas[data.formula_index]
    row.selected_formula_index = data.formula_index
    row.formula_json = json.dumps(variant["formula"], ensure_ascii=False)
    row.lab_report_json = json.dumps(variant["lab_report"], ensure_ascii=False)
    row.missing_materials_json = json.dumps(variant["missing_materials"], ensure_ascii=False)
    row.status = variant["status"]
    audit(session, user, "cosmetic_formula.selected", "cosmetic_request", row.id, {"formula_index": data.formula_index})
    await session.commit()
    await session.refresh(row)
    return request_dict(row)


@router.post("/admin/cosmetic-requests/{request_id}/conversation")
async def discuss_formula(request_id: int, data: FormulaConversationWrite, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)], background_tasks: BackgroundTasks = None):
    row = await session.get(CosmeticRequest, request_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demande introuvable")
    if row.status == "approved": raise HTTPException(409, "La formule validée ne peut plus être modifiée")
    formulas = _json(row.formulas_json, [])
    if not formulas and row.formula_json:
        formulas = [{"version": row.revision, "formula": _json(row.formula_json, {}), "lab_report": _json(row.lab_report_json, {}), "missing_materials": _json(row.missing_materials_json, []), "status": row.status}]
    if data.formula_index >= len(formulas):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Formule introuvable")
    conversation = _json(row.conversation_json, [])
    variant = formulas[data.formula_index]
    now = datetime.now(UTC).isoformat()
    conversation.append({"role": "admin", "message": data.message.strip(), "formula_index": data.formula_index, "created_at": now})
    agent_result = await LaboratoryAgentService().discuss(
        message=data.message.strip(),
        formula=variant["formula"],
        report=variant["lab_report"],
        conversation=conversation,
    )
    revised = False
    if agent_result["action"] == "revise":
        answers = _json(row.answers_json, {})
        memory_row = await session.get(SiteSetting, "cosmetic_formula_memory")
        approved_history = list((memory_row.value or {}).get("approved", [])) if memory_row else []
        materials = list((await session.scalars(select(RawMaterial).where(RawMaterial.is_active.is_(True)))).all())
        feedback = "\n".join(filter(None, [row.admin_feedback, data.message.strip()]))
        proposal = await LaboratoryAgentService().generate(
            product_idea=row.product_type,
            needs=row.needs,
            answers=answers,
            materials=materials,
            approved_history=approved_history,
            admin_feedback=feedback,
            material_decision=_json(row.material_decision_json, {}),
            variation_index=data.formula_index,
            previous_suggestions=[{"current_formula": variant["formula"]}],
        )
        row.revision += 1
        variant = _build_formula_variant(
            proposal,
            request=row,
            materials=materials,
            answers=answers,
            approved_history=approved_history,
            version=row.revision,
        )
        if background_tasks is not None:
            variant["lab_report"]["process_status"] = "generating"
            variant["lab_report"]["process_job_id"] = secrets.token_hex(12)
        formulas[data.formula_index] = variant
        row.formulas_json = json.dumps(formulas, ensure_ascii=False)
        row.selected_formula_index = data.formula_index
        row.formula_json = json.dumps(variant["formula"], ensure_ascii=False)
        row.lab_report_json = json.dumps(variant["lab_report"], ensure_ascii=False)
        row.missing_materials_json = json.dumps(variant["missing_materials"], ensure_ascii=False)
        row.status = variant["status"]
        row.admin_feedback = data.message.strip()
        revised = True
    conversation.append({"role": "agent", "message": agent_result["reply"], "formula_index": data.formula_index, "action": agent_result["action"], "version": variant.get("version"), "created_at": datetime.now(UTC).isoformat()})
    row.conversation_json = json.dumps(conversation[-100:], ensure_ascii=False)
    audit(session, user, "cosmetic_formula.discussed", "cosmetic_request", row.id, {"formula_index": data.formula_index, "action": agent_result["action"], "revised": revised})
    await session.commit()
    await session.refresh(row)
    if revised and background_tasks is not None:
        job_id = variant["lab_report"]["process_job_id"]
        background_tasks.add_task(run_manufacturing_procedure, row.id, data.formula_index, job_id)
    return request_dict(row)


@router.post("/admin/cosmetic-requests/{request_id}/approve")
async def approve_formula(
    request_id: int, data: FormulaApprovalWrite, background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(require_roles("admin"))],
    session: Annotated[AsyncSession, Depends(get_sqlite_session)],
):
    row = await session.get(CosmeticRequest, request_id)
    if not row: raise HTTPException(status.HTTP_404_NOT_FOUND, "Demande introuvable")
    if row.status == "approved": return request_dict(row)
    formula = _json(row.formula_json, None)
    report = _json(row.lab_report_json, {})
    if report.get("process_status") == "generating":
        raise HTTPException(409, "Attendez la fin de la génération du procédé avant validation")
    if report.get("process_status") == "failed" or not report.get("manufacturing_steps"):
        raise HTTPException(409, "Le procédé détaillé doit être complet avant validation. Réessayez sa génération.")
    decision = _json(row.material_decision_json, {})
    missing = _json(row.missing_materials_json, [])
    procurement_approved = (decision.get("can_source") is True
        and decision.get("formula_index", row.selected_formula_index) == row.selected_formula_index
        and decision.get("revision", row.revision) == row.revision)
    if not formula or row.status not in {"draft_ready", "materials_to_source", "needs_materials"} or (missing and not procurement_approved):
        raise HTTPException(status.HTTP_409_CONFLICT, "Validez l'approvisionnement des matières manquantes ou choisissez une formule complète avant validation.")
    if abs(_number(formula.get("total_percentage"), 0) - 100) > 0.01:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La formule ne totalise pas 100 %.")
    ingredients = formula.get("ingredients") or []
    if len(ingredients) < 2 or any(_number(item.get("percentage"), 0) <= 0 for item in ingredients) or abs(sum(_number(item.get("percentage"), 0) for item in ingredients) - 100) > 0.01:
        raise HTTPException(422, "La formule quantitative doit contenir des matières dosées totalisant 100 %")
    product = None
    if row.product_id:
        product = await ProductService().get_product(row.product_id)
    else:
        packaging = report.get("packaging") or []
        packaging_text = ", ".join(map(str, packaging)) if isinstance(packaging, list) else str(packaging)
        description = f"Produit personnalisé pour {row.client_name} — dossier {row.reference}. {report.get('summary', '')} Packaging demandé : {packaging_text or 'à proposer'}.".strip()
        product = await ProductService().create_product(ProductCreate(brand="MIELMAR", name=data.product_name.strip(), form_type=row.product_type, description=description, category=data.category or "Cosmétique", price=data.price, currency="MAD", stock=0, is_active=False, images=[], videos=[], tags=["sur-mesure", row.reference.lower()], custom_client_name=row.client_name, custom_client_user_id=row.user_id, cosmetic_request_reference=row.reference))
        row.product_id = product.product_id
    row.status = "approved"; row.approved_by = user.id; row.approved_at = datetime.now(UTC)
    memory = await session.get(SiteSetting, "cosmetic_formula_memory")
    history = list((memory.value or {}).get("approved", [])) if memory else []
    history.append({"request_reference": row.reference, "client_name": row.client_name, "user_id": row.user_id, "product_id": row.product_id, "product_type": row.product_type, "formula": formula, "admin_feedback": row.admin_feedback, "approved_at": row.approved_at.isoformat()})
    value = {"approved": history[-50:]}
    if memory: memory.value = value
    else: session.add(SiteSetting(key="cosmetic_formula_memory", value=value))
    media_request_id = None
    if data.media_mode == "agent":
        media = await ProductMediaAgentService(session).prepare(ProductMediaPrepareRequest(product_id=product.product_id, source_mode="agent", language="fr", visual_style=data.visual_style, requested_media=["image", "video"], image_description=data.image_description or f"Packshot professionnel de {data.product_name}, packaging MIELMAR adapté à {row.product_type}.", video_description=data.video_description or f"Vidéo produit courte et sobre de {data.product_name}, avec le même packaging et un mouvement lent."), user.id)
        media_request_id = media.id
        if media.status == "queued": background_tasks.add_task(run_local_product_media_generation, media.id)
    audit(session, user, "cosmetic_formula.approved", "cosmetic_request", row.id, {"product_id": row.product_id, "media_mode": data.media_mode, "media_request_id": media_request_id})
    session.add(Notification(target_role="admin", notification_type="custom_product_created", title=f"Produit créé · {data.product_name}", message="Le produit reste désactivé jusqu’à validation de son prix, stock, packaging et médias.", link=f"/admin?tab=products&product={row.product_id}"))
    await session.commit(); await session.refresh(row)
    result = request_dict(row); result["media_request_id"] = media_request_id
    return result


@router.post("/admin/cosmetic-requests/{request_id}/procedure")
async def generate_manufacturing_procedure(request_id: int, background_tasks: BackgroundTasks, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)]):
    row = await session.get(CosmeticRequest, request_id)
    if not row: raise HTTPException(404, "Demande introuvable")
    formula = _json(row.formula_json, None)
    if not formula: raise HTTPException(409, "Générez d'abord une formule")
    if row.status == "approved": raise HTTPException(409, "Le dossier validé est archivé")
    report = _json(row.lab_report_json, {})
    if report.get("process_status") == "generating":
        job_id = str(report.get("process_job_id") or "")
        if job_id and job_id not in ACTIVE_PROCEDURE_JOBS:
            background_tasks.add_task(
                run_manufacturing_procedure,
                row.id,
                row.selected_formula_index,
                job_id,
            )
        return request_dict(row)
    job_id = secrets.token_hex(12)
    report = {**report, "process_status": "generating", "process_job_id": job_id, "process_error": None}
    row.lab_report_json = json.dumps(report, ensure_ascii=False)
    variants = _json(row.formulas_json, [])
    if variants:
        variants[row.selected_formula_index]["lab_report"] = report
        row.formulas_json = json.dumps(variants, ensure_ascii=False)
    audit(session, user, "cosmetic_procedure.queued", "cosmetic_request", row.id, {"formula_index": row.selected_formula_index})
    await session.commit(); await session.refresh(row)
    background_tasks.add_task(run_manufacturing_procedure, row.id, row.selected_formula_index, job_id)
    return request_dict(row)


async def run_manufacturing_procedure(request_id: int, formula_index: int, job_id: str):
    ACTIVE_PROCEDURE_JOBS.add(job_id)
    try:
        async with SqliteSession() as session:
            row = await session.get(CosmeticRequest, request_id)
            if not row: return
            variants = _json(row.formulas_json, [])
            variant = variants[formula_index] if formula_index < len(variants) else None
            report = variant["lab_report"] if variant else _json(row.lab_report_json, {})
            if report.get("process_job_id") != job_id: return
            formula = variant["formula"] if variant else _json(row.formula_json, {})
            brief = {"product_idea": row.product_type, "needs": row.needs, "answers": _json(row.answers_json, {})}
        try:
            result = build_local_manufacturing_plan(formula=formula, brief=brief)
            result["process_error"] = None
        except Exception:
            result = {"manufacturing_steps": [], "manufacturing_process": [], "process_status": "failed", "process_error": "Le procédé détaillé n'a pas pu être généré. Réessayez."}
        async with SqliteSession() as session:
            row = await session.get(CosmeticRequest, request_id)
            if not row: return
            variants = _json(row.formulas_json, [])
            if variants:
                if formula_index >= len(variants): return
                report = variants[formula_index]["lab_report"]
            else:
                report = _json(row.lab_report_json, {})
            if report.get("process_job_id") != job_id: return
            report = {**report, **result}
            if variants:
                variants[formula_index]["lab_report"] = report
                row.formulas_json = json.dumps(variants, ensure_ascii=False)
            if row.selected_formula_index == formula_index:
                row.lab_report_json = json.dumps(report, ensure_ascii=False)
            if result.get("process_status") == "proposed":
                session.add(Notification(
                    target_role="admin",
                    notification_type="cosmetic_procedure_ready",
                    title=f"Procédé prêt · {row.reference}",
                    message="Les phases détaillées sont prêtes. Vous pouvez contrôler puis valider la formule.",
                    link=f"/admin?tab=formulation-requests&request={row.id}",
                ))
            await session.commit()
    finally:
        ACTIVE_PROCEDURE_JOBS.discard(job_id)


@router.get("/admin/cosmetic-requests/{request_id}/word")
async def download_formulation_word(request_id: int, user: Annotated[User, Depends(require_roles("admin"))], session: Annotated[AsyncSession, Depends(get_sqlite_session)], document: Literal["cahier", "procedure"] = "procedure"):
    row = await session.get(CosmeticRequest, request_id)
    if not row: raise HTTPException(404, "Demande introuvable")
    dossier = request_dict(row)
    if document == "procedure" and not dossier["formula"]:
        raise HTTPException(409, "Générez d'abord une formule")
    if document == "procedure" and (dossier.get("lab_report") or {}).get("process_status") == "generating":
        raise HTTPException(409, "Le procédé détaillé est en cours de génération")
    if document == "procedure" and ((dossier.get("lab_report") or {}).get("process_status") == "failed" or not (dossier.get("lab_report") or {}).get("manufacturing_steps")):
        raise HTTPException(409, "Le procédé détaillé doit être complet avant son export Word")
    return Response(build_formulation_document(dossier, document), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f'attachment; filename="MIELMAR-{row.reference}-{document}.docx"', "Cache-Control": "no-store"})
