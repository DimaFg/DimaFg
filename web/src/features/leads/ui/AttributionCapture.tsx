"use client";

import { useEffect } from "react";

import { captureAttribution } from "@/features/leads/model/attribution";

export function AttributionCapture() {
  useEffect(() => {
    captureAttribution();
  }, []);
  return null;
}
