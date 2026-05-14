#!/usr/bin/env python3
"""
Assign a nearest named target to each von Neumann probe vector.

This is intended as a one-off data enrichment pass. It duplicates the probe
swarm math from app/renderer.js, reads proper-name objects from the existing HYG raw
catalog plus processed landmarks, and writes the resulting table into
data/processed/metadata.json as "probeVectorIntersections".

Usage:
    python3 pipeline/name_probe_vectors.py
"""

from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass
from typing import Any


PC_TO_LY = 3.26156
PROBE_COUNT = 997
PROBE_VELOCITY = 0.05
PROBE_PLANE_BIAS_EXPONENT = 2.35
GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_HYG = os.path.join(ROOT_DIR, "data", "raw", "hygdata_v41.csv")
METADATA_PATH = os.path.join(ROOT_DIR, "data", "processed", "metadata.json")
LANDMARKS_PATH = os.path.join(ROOT_DIR, "data", "processed", "landmarks.json")


@dataclass(frozen=True)
class Target:
    name: str
    kind: str
    index: int | None
    x: float
    y: float
    z: float
    app_mag: float | None = None
    description: str | None = None

    @property
    def distance_ly(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    @property
    def unit(self) -> tuple[float, float, float]:
        distance = self.distance_ly
        return (self.x / distance, self.y / distance, self.z / distance)


def parse_float(value: str | None, default: float | None = None) -> float | None:
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def normalize(x: float, y: float, z: float) -> tuple[float, float, float]:
    length = math.sqrt(x * x + y * y + z * z)
    return (x / length, y / length, z / length)


def galactic_coordinates(direction: tuple[float, float, float]) -> dict[str, float]:
    x, y, z = direction
    longitude = (math.degrees(math.atan2(y, x)) + 360) % 360
    latitude = math.degrees(math.asin(max(-1, min(1, z))))
    return {"longitude": longitude, "latitude": latitude}


def generate_probe_swarm(count: int) -> list[dict[str, Any]]:
    probes = []
    for index in range(count):
        centered = ((index + 0.5) / count) * 2 - 1
        biased_z = math.copysign(abs(centered) ** PROBE_PLANE_BIAS_EXPONENT, centered)
        radius = math.sqrt(max(0, 1 - biased_z * biased_z))
        longitude = index * GOLDEN_ANGLE
        direction = normalize(
            math.cos(longitude) * radius,
            math.sin(longitude) * radius,
            biased_z,
        )
        coords = galactic_coordinates(direction)
        probes.append({
            "index": index,
            "name": f"Probe {index + 1:04d}",
            "direction": direction,
            "velocity": PROBE_VELOCITY,
            "longitude": coords["longitude"],
            "latitude": coords["latitude"],
        })
    return probes


def star_name(row: dict[str, str]) -> str:
    return (row.get("proper") or "").strip()


def read_star_targets() -> list[Target]:
    targets: list[Target] = []
    processed_index = 0
    with open(RAW_HYG, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            x_pc = parse_float(row.get("x"))
            y_pc = parse_float(row.get("y"))
            z_pc = parse_float(row.get("z"))
            if x_pc is None or y_pc is None or z_pc is None:
                continue

            abs_mag = parse_float(row.get("absmag"))
            app_mag = parse_float(row.get("mag"))
            if abs_mag is None or app_mag is None:
                continue

            name = star_name(row)
            x = x_pc * PC_TO_LY
            y = y_pc * PC_TO_LY
            z = z_pc * PC_TO_LY
            if not name or name == "Sol" or (x == 0 and y == 0 and z == 0):
                processed_index += 1
                continue

            targets.append(Target(
                name=name,
                kind="star",
                index=processed_index,
                x=x,
                y=y,
                z=z,
                app_mag=app_mag,
            ))
            processed_index += 1
    return targets


def read_landmark_targets() -> list[Target]:
    with open(LANDMARKS_PATH, "r", encoding="utf-8") as handle:
        landmarks = json.load(handle)

    targets = []
    for point in landmarks.get("points", []):
        x = float(point["x"])
        y = float(point["y"])
        z = float(point["z"])
        if x == 0 and y == 0 and z == 0:
            continue
        targets.append(Target(
            name=str(point["name"]),
            kind="landmark",
            index=None,
            x=x,
            y=y,
            z=z,
            description=point.get("description"),
        ))
    return targets


def angular_match(probe: dict[str, Any], targets: list[Target]) -> dict[str, Any]:
    direction = probe["direction"]
    best_target: Target | None = None
    best_dot = -2.0

    for target in targets:
        ux, uy, uz = target.unit
        dot = direction[0] * ux + direction[1] * uy + direction[2] * uz
        if dot > best_dot:
            best_dot = dot
            best_target = target

    if best_target is None:
        raise RuntimeError("No target found")

    clamped_dot = max(-1, min(1, best_dot))
    angle_rad = math.acos(clamped_dot)
    distance = best_target.distance_ly
    axial_distance = distance * clamped_dot
    perpendicular_offset = distance * math.sin(angle_rad)

    target: dict[str, Any] = {
        "name": best_target.name,
        "kind": best_target.kind,
        "index": best_target.index,
        "position": {
            "x": round(best_target.x, 6),
            "y": round(best_target.y, 6),
            "z": round(best_target.z, 6),
        },
        "distanceLy": round(distance, 6),
        "angularSeparationDeg": round(math.degrees(angle_rad), 9),
        "axialDistanceLy": round(axial_distance, 6),
        "perpendicularOffsetLy": round(perpendicular_offset, 6),
    }
    if best_target.app_mag is not None:
        target["appMag"] = best_target.app_mag
    if best_target.description:
        target["description"] = best_target.description

    return {
        "probeIndex": probe["index"],
        "probeName": probe["name"],
        "direction": {
            "x": round(direction[0], 12),
            "y": round(direction[1], 12),
            "z": round(direction[2], 12),
        },
        "galacticLongitudeDeg": round(probe["longitude"], 9),
        "galacticLatitudeDeg": round(probe["latitude"], 9),
        "target": target,
    }


def main() -> int:
    if not os.path.exists(RAW_HYG):
        raise SystemExit(f"Missing raw HYG catalog: {RAW_HYG}")
    if not os.path.exists(METADATA_PATH):
        raise SystemExit(f"Missing metadata file: {METADATA_PATH}")
    if not os.path.exists(LANDMARKS_PATH):
        raise SystemExit(f"Missing landmarks file: {LANDMARKS_PATH}")

    probes = generate_probe_swarm(PROBE_COUNT)
    targets = read_star_targets() + read_landmark_targets()
    print(f"Loaded {len(targets):,} named targets")
    print(f"Matching {len(probes):,} probe vectors")

    intersections = [angular_match(probe, targets) for probe in probes]

    with open(METADATA_PATH, "r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    metadata["probeVectorIntersections"] = {
        "description": "Nearest proper-name target by angular separation for each deterministic probe vector.",
        "probeCount": PROBE_COUNT,
        "matching": "maximum dot product between the probe unit vector and target unit vector from Sol",
        "targets": "HYG stars with proper names plus processed landmark points; Sol is excluded",
        "items": intersections,
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")

    print(f"Wrote {METADATA_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
