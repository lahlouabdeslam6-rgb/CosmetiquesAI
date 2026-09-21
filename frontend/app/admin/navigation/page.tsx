"use client";

import { useEffect } from "react";

export default function RemovedAdminPage() {
  useEffect(() => {
    window.location.replace("/admin");
  }, []);

  return <main className="page-loading">Retour vers l'administration...</main>;
}
