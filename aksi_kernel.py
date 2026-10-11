"""AKSI MATRIX numerical kernel (classical, NumPy/SciPy).

This module implements:
- a small conditional RBM/QBM-inspired thermodynamic model;
- Gershgorin-disc diagnostics for complex weight matrices;
- canonical SHA-256 integrity receipts.

Important scientific boundary:
This is a classical statistical-mechanics-inspired model, not a physical quantum
computer or a claim of quantum advantage. H_eff is an explicitly defined
dimensionless diagnostic index, not experimentally measured quantum coherence.
The 97% Gershgorin setting is a configurable engineering threshold, not a
probability that a system is safe or stable in every operational sense.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray
from scipy.special import logsumexp


FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


def _canonical_json(value: Any) -> str:
    """Serialize nested JSON-compatible values deterministically."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _finite_float(name: str, value: float, *, minimum: float, maximum: float) -> float:
    value = float(value)
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be finite and in [{minimum}, {maximum}]")
    return value


@dataclass(frozen=True)
class QBMResult:
    """Thermodynamic diagnostics for one input string."""
    energy: float
    free_energy: float
    partition_function: float
    log_partition_function: float
    effective_coherence: float
    entropy: float
    entropy_ratio: float
    empathy: float
    coherence: float
    byte_length: int
    visible_state: tuple[float, ...]


class QuantumBoltzmannMachine:
    """Vectorized classical RBM-inspired thermodynamic model.

    UTF-8 bytes are reduced to a fixed-size visible spin vector in [-1, 1].
    The hidden layer has 2**hidden_units possible bipolar states; exact
    enumeration is practical because hidden_units is deliberately bounded.
    NumPy performs vector operations and SciPy supplies stable log-sum-exp.
    """

    def __init__(
        self,
        visible_units: int = 8,
        hidden_units: int = 8,
        beta: float = 1.0,
        empathy_weight: float = 0.25,
        coherence_weight: float = 0.50,
        seed: int = 14021995,
    ) -> None:
        if visible_units < 4 or visible_units > 64:
            raise ValueError("visible_units must be between 4 and 64")
        if hidden_units < 1 or hidden_units > 12:
            raise ValueError("hidden_units must be between 1 and 12 (exact enumeration)")
        self.visible_units = int(visible_units)
        self.hidden_units = int(hidden_units)
        self.beta = _finite_float("beta", beta, minimum=1e-9, maximum=1e6)
        self.empathy_weight = _finite_float(
            "empathy_weight", empathy_weight, minimum=-1e3, maximum=1e3
        )
        self.coherence_weight = _finite_float(
            "coherence_weight", coherence_weight, minimum=-1e3, maximum=1e3
        )

        rng = np.random.default_rng(seed)
        scale = 1.0 / math.sqrt(self.visible_units + self.hidden_units)
        self.weights: FloatArray = rng.normal(
            0.0, scale, (self.visible_units, self.hidden_units)
        ).astype(np.float64)
        self.visible_bias: FloatArray = np.zeros(self.visible_units, dtype=np.float64)
        self.hidden_bias: FloatArray = np.zeros(self.hidden_units, dtype=np.float64)
        # Enumerate all bipolar hidden states once; matrix math is vectorized.
        self._hidden_states: FloatArray = (
            2 * np.array(
                list(itertools.product((0.0, 1.0), repeat=self.hidden_units)),
                dtype=np.float64,
            ) - 1
        )

    def encode_text(self, text: str) -> tuple[FloatArray, int]:
        """Convert text to UTF-8 bytes and compress it to a fixed spin vector."""
        if not isinstance(text, str):
            raise TypeError("text must be str")
        raw = np.frombuffer(text.encode("utf-8"), dtype=np.uint8)
        if raw.size == 0:
            raw = np.array([0], dtype=np.uint8)
        normalized = raw.astype(np.float64) / 127.5 - 1.0
        chunks = np.array_split(normalized, self.visible_units)
        visible = np.array(
            [float(chunk.mean()) if chunk.size else 0.0 for chunk in chunks],
            dtype=np.float64,
        )
        return np.clip(visible, -1.0, 1.0), int(raw.size)

    def calculate(
        self,
        text: str,
        *,
        empathy: float = 0.5,
        coherence: float = 0.5,
    ) -> QBMResult:
        """Calculate E, F, Z and H_eff for a text-derived visible state.

        E is the Gibbs expected energy over the hidden states conditioned on
        the visible input. Z is the corresponding conditional partition
        function. H_eff = (1 - normalized_entropy) * (0.5 + 0.5*coherence)
        * (0.5 + 0.5*empathy), clipped to [0, 1].
        """
        empathy = _finite_float("empathy", empathy, minimum=0.0, maximum=1.0)
        coherence = _finite_float("coherence", coherence, minimum=0.0, maximum=1.0)
        visible, byte_length = self.encode_text(text)

        # E(v,h) = -vWh - bv.v - bh.h - empathy_term - coherence_term
        interaction = self._hidden_states @ self.weights.T
        interaction = interaction @ visible
        hidden_field = self._hidden_states @ self.hidden_bias
        visible_field = float(self.visible_bias @ visible)
        energies = (
            -interaction
            - visible_field
            - hidden_field
            - self.empathy_weight * empathy
            - self.coherence_weight * coherence
        )

        log_weights = -self.beta * energies
        log_z = float(logsumexp(log_weights))
        probabilities = np.exp(log_weights - log_z)
        mean_energy = float(probabilities @ energies)
        free_energy = float(-log_z / self.beta)
        entropy = float(-np.sum(probabilities * np.log(np.maximum(probabilities, 1e-300))))
        max_entropy = math.log(self._hidden_states.shape[0])
        entropy_ratio = float(np.clip(entropy / max_entropy, 0.0, 1.0)) if max_entropy else 0.0
        h_eff = float(np.clip(
            (1.0 - entropy_ratio) * (0.5 + 0.5 * coherence) * (0.5 + 0.5 * empathy),
            0.0,
            1.0,
        ))
        # Avoid floating-point overflow while retaining log(Z) as the stable value.
        partition = math.exp(log_z) if log_z <= math.log(np.finfo(float).max) else math.inf

        return QBMResult(
            energy=mean_energy,
            free_energy=free_energy,
            partition_function=float(partition),
            log_partition_function=log_z,
            effective_coherence=h_eff,
            entropy=entropy,
            entropy_ratio=entropy_ratio,
            empathy=empathy,
            coherence=coherence,
            byte_length=byte_length,
            visible_state=tuple(float(x) for x in visible),
        )


@dataclass(frozen=True)
class GershgorinDisc:
    """One Gershgorin disc: complex diagonal center and row-sum radius."""
    index: int
    center_real: float
    center_imag: float
    radius: float

    @property
    def center_abs(self) -> float:
        return math.hypot(self.center_real, self.center_imag)

    @property
    def outer_radius(self) -> float:
        return self.center_abs + self.radius


@dataclass(frozen=True)
class GershgorinResult:
    """Gershgorin localization and configurable origin-centered bound."""
    discs: tuple[GershgorinDisc, ...]
    stability_radius: float
    stable: bool
    stable_percent: float
    status: str


class GershgorinStability:
    """Gershgorin-circle diagnostics for 4x4 or 8x8 complex matrices.

    A matrix is inside the configured bound when |center_i| + radius_i is
    <= stability_radius for every row. This is a sufficient localization
    criterion relative to the chosen disk, not a universal stability proof.
    """

    @staticmethod
    def analyze(
        weights: Sequence[Sequence[complex]] | NDArray[Any],
        *,
        stability_radius: float = 0.97,
    ) -> GershgorinResult:
        limit = _finite_float(
            "stability_radius", stability_radius, minimum=1e-12, maximum=1e12
        )
        matrix = np.asarray(weights, dtype=np.complex128)
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError("weights must be a square matrix")
        if matrix.shape[0] not in (4, 8):
            raise ValueError("weights matrix size must be 4x4 or 8x8")
        if not np.all(np.isfinite(matrix.real)) or not np.all(np.isfinite(matrix.imag)):
            raise ValueError("weights must contain only finite values")

        row_sums = np.sum(np.abs(matrix), axis=1) - np.abs(np.diag(matrix))
        discs = tuple(
            GershgorinDisc(
                index=i,
                center_real=float(matrix[i, i].real),
                center_imag=float(matrix[i, i].imag),
                radius=float(max(0.0, row_sums[i])),
            )
            for i in range(matrix.shape[0])
        )
        maximum_outer = max(d.outer_radius for d in discs)
        stable = all(d.outer_radius <= limit + 1e-12 for d in discs)
        stable_percent = float(np.clip(100.0 * (1.0 - maximum_outer / limit), 0.0, 100.0))
        status = (
            f"Стабильное состояние (порог {limit * 100:.1f}%)"
            if stable else "Нестабильное относительно заданной границы"
        )
        return GershgorinResult(
            discs=discs,
            stability_radius=limit,
            stable=stable,
            stable_percent=stable_percent,
            status=status,
        )


class SovereignProof:
    """Create and verify SHA-256 integrity receipts for recorded diagnostics.

    The digest commits to the data and nonce. It proves integrity of this
    serialized record only; it does not prove that the model is scientifically
    correct, that a result is true, or that the caller has a trusted identity.
    """

    @staticmethod
    def _timestamp(value: str | datetime | None) -> str:
        if value is None:
            return datetime.now(timezone.utc).isoformat()
        if isinstance(value, datetime):
            dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        if isinstance(value, str) and value.strip():
            return value.strip()
        raise ValueError("timestamp must be a non-empty string, datetime, or None")

    @classmethod
    def generate(
        cls,
        qbm: QBMResult | Mapping[str, Any],
        gershgorin: GershgorinResult | Mapping[str, Any],
        timestamp: str | datetime | None = None,
    ) -> dict[str, Any]:
        qbm_data = asdict(qbm) if isinstance(qbm, QBMResult) else dict(qbm)
        if isinstance(gershgorin, GershgorinResult):
            g_data = {
                "discs": [asdict(d) for d in gershgorin.discs],
                "stability_radius": gershgorin.stability_radius,
                "stable": gershgorin.stable,
                "stable_percent": gershgorin.stable_percent,
                "status": gershgorin.status,
            }
        else:
            g_data = dict(gershgorin)

        payload = {
            "protocol": "AKSI-MATRIX-PROOF/1",
            "timestamp": cls._timestamp(timestamp),
            "nonce": secrets.token_hex(16),
            "qbm": qbm_data,
            "gershgorin": g_data,
        }
        digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
        return {
            **payload,
            "sha256": digest,
            "key_prefix": digest[:8].upper(),
            "status": "✓ verified",
            "claim_boundary": (
                "SHA-256 confirms record integrity when verified; it does not establish "
                "scientific truth, physical quantum behavior, or trusted identity."
            ),
        }

    @staticmethod
    def verify(proof: Mapping[str, Any]) -> bool:
        """Recompute the digest and compare it with the stored SHA-256 value."""
        try:
            payload = {
                key: value for key, value in proof.items()
                if key not in {"sha256", "key_prefix", "status", "claim_boundary"}
            }
            expected = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
            return secrets.compare_digest(expected, str(proof.get("sha256", "")))
        except (TypeError, ValueError):
            return False


def demo() -> None:
    """Run a reproducible local demonstration."""
    request = "AKSI MATRIX: оценить когерентность, устойчивость и целостность результата."
    qbm = QuantumBoltzmannMachine(visible_units=8, hidden_units=8)
    thermo = qbm.calculate(request, empathy=0.72, coherence=0.81)

    # A bounded complex matrix for a transparent Gershgorin demonstration.
    weights = np.array([
        [0.10 + 0.02j, 0.03, 0.02j, 0.01],
        [0.02, 0.12 - 0.01j, 0.02, 0.01j],
        [0.01j, 0.02, 0.08, 0.03],
        [0.01, 0.01j, 0.02, 0.09 + 0.01j],
    ], dtype=np.complex128)
    stability = GershgorinStability.analyze(weights, stability_radius=0.97)
    proof = SovereignProof.generate(thermo, stability)

    print("=== AKSI MATRIX · Classical Numerical Kernel ===")
    print(f"Request: {request}")
    print(f"UTF-8 bytes: {thermo.byte_length}")
    print(f"E (expected energy): {thermo.energy:.8f}")
    print(f"F (free energy): {thermo.free_energy:.8f}")
    print(f"Z (partition function): {thermo.partition_function:.8f}")
    print(f"log(Z): {thermo.log_partition_function:.8f}")
    print(f"H_eff: {thermo.effective_coherence:.6f}")
    print("\nGershgorin discs:")
    for disc in stability.discs:
        center = complex(disc.center_real, disc.center_imag)
        print(f"  row={disc.index}: center={center!s}, radius={disc.radius:.6f}")
    print(f"Stable: {stability.stable} — {stability.status}")
    print("\nCryptographic proof:")
    print(f"  key: {proof['key_prefix']}")
    print(f"  sha256: {proof['sha256']}")
    print(f"  status: {proof['status']}")
    print(f"  proof self-check: {SovereignProof.verify(proof)}")


if __name__ == "__main__":
    demo()
