"""Physics-based synthetic wind turbine telemetry generator (NREL 5MW Baseline Model).

Generates realistic time-series SCADA datasets covering sub-rated, rated, gust,
startup, shutdown, and fault injection test benches.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd

# Add repository root to pythonpath
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app.core.config import settings
from backend.app.services.fault_injection import FaultConfig, FaultInjectionEngine, FaultType


def simulate_turbine_run(
    scenario: str = "normal_run",
    duration_sec: float = 60.0,
    dt: float = 0.05,
    seed: int = 42,
) -> pd.DataFrame:
    """Simulate aeromechanical and electrical dynamics of NREL 5MW turbine."""
    rng = np.random.default_rng(seed)
    n_steps = int(duration_sec / dt)
    time = np.linspace(0.0, duration_sec, n_steps)

    # 1. Wind Speed Generation
    if scenario == "gust_event" or "overspeed" in scenario or "pitch_delay" in scenario:
        # IEC Extreme Operating Gust (EOG) profile
        t_gust = duration_sec / 2.0
        v_base = 11.0
        gust_amplitude = 7.0
        gust_width = 12.0
        wind = v_base + gust_amplitude * np.exp(-((time - t_gust) ** 2) / (2 * (gust_width / 3.0) ** 2))
        wind += rng.normal(0.0, 0.25, size=n_steps)
    elif scenario == "startup":
        # Ramp from 2.0 m/s to 9.0 m/s
        wind = 2.0 + (7.0 * (time / duration_sec)) + rng.normal(0.0, 0.15, size=n_steps)
    elif scenario == "shutdown":
        # Operating at 12 m/s then shutdown commanded
        wind = 12.0 + rng.normal(0.0, 0.25, size=n_steps)
    elif scenario == "above_rated":
        wind = 16.0 + rng.normal(0.0, 0.4, size=n_steps)
    elif scenario == "below_rated":
        wind = 7.5 + rng.normal(0.0, 0.3, size=n_steps)
    else:  # normal_run
        # Region 2 to 2.5 transition wind: 9.0 to 12.0 m/s
        wind = 9.5 + 2.0 * np.sin(2 * np.pi * 0.02 * time) + rng.normal(0.0, 0.2, size=n_steps)

    wind = np.clip(wind, 0.1, 35.0)

    # 2. Dynamic State Variables Initialization
    omega_rotor = np.zeros(n_steps)    # RPM
    pitch = np.zeros(n_steps)          # Degrees
    torque_gen = np.zeros(n_steps)     # Nm
    power_kw = np.zeros(n_steps)       # kW
    tower_accel = np.zeros(n_steps)    # m/s^2
    yaw_error = np.zeros(n_steps)      # deg
    state_str = []
    fault_flags = np.zeros(n_steps, dtype=int)

    # Initial states
    current_rpm = 12.1 if scenario not in ["startup"] else 3.0
    current_pitch = 0.0
    pitch_integral = 0.0

    gearbox_ratio = settings.turbine.gearbox_ratio  # 97.0
    rated_rpm = settings.turbine.rated_rotor_speed_rpm    # 12.1
    rated_torque = settings.turbine.rated_generator_torque_nm  # 43093.55
    max_pitch_rate = settings.turbine.max_pitch_rate_dps       # 8.0 deg/s

    for i in range(n_steps):
        t = time[i]
        v_w = wind[i]

        # Supervisory State Logic
        if scenario == "startup" and t < 15.0:
            c_state = "STARTUP"
            target_rpm = min(rated_rpm, 3.0 + (rated_rpm - 3.0) * (t / 15.0))
            current_rpm += (target_rpm - current_rpm) * 0.05
            cmd_pitch = max(0.0, 80.0 * (1.0 - t / 15.0))
            cmd_torque = 5000.0 * (t / 15.0)
        elif scenario == "shutdown" and t > 30.0:
            c_state = "SHUTDOWN"
            current_rpm = max(0.0, current_rpm - 0.25 * dt)
            cmd_pitch = min(90.0, current_pitch + 8.0 * dt)
            cmd_torque = max(0.0, torque_gen[max(0, i - 1)] - 2000.0 * dt)
        elif v_w < settings.turbine.rated_wind_speed_mps:
            c_state = "BELOW_RATED"
            cmd_pitch = 0.0
            # Region 2 optimal torque control: T_gen = k * (omega_gen)^2
            gen_speed_rpm = current_rpm * gearbox_ratio
            k_opt = 0.031  # Nm / (rpm^2)
            cmd_torque = min(rated_torque, k_opt * (gen_speed_rpm ** 2))
            # Speed equilibrium
            target_rpm = 6.9 + (12.1 - 6.9) * ((v_w - 3.0) / (11.4 - 3.0))
            current_rpm += (target_rpm - current_rpm) * (0.8 * dt)
        else:
            c_state = "RATED_POWER"
            cmd_torque = rated_torque
            # Region 3 PI pitch controller regulating rotor speed to 12.1 RPM
            speed_err = current_rpm - rated_rpm
            pitch_integral += speed_err * dt
            kp = 2.5
            ki = 0.8
            # Aerodynamic pitch demand
            base_pitch = (v_w - 11.4) * 1.55
            cmd_pitch = np.clip(base_pitch + kp * speed_err + ki * pitch_integral, 0.0, 85.0)
            # Rotor acceleration balance
            excess_wind = max(0.0, v_w - 11.4)
            rpm_drift = 0.25 * (excess_wind - 0.8 * cmd_pitch)
            current_rpm += rpm_drift * dt

        # Pitch actuator rate limit dynamics
        pitch_diff = cmd_pitch - current_pitch
        max_step = max_pitch_rate * dt
        current_pitch += np.clip(pitch_diff, -max_step, max_step)
        pitch[i] = current_pitch

        # Filtered torque response with 1st-order converter time constant (tau = 0.35s)
        alpha_torque = min(1.0, dt / 0.35)
        current_torque = (
            cmd_torque if i == 0 else torque_gen[i - 1] + (cmd_torque - torque_gen[i - 1]) * alpha_torque
        )
        torque_gen[i] = current_torque

        # Rotor and generator velocities
        current_rpm += rng.normal(0.0, 0.005)
        omega_rotor[i] = max(0.0, current_rpm)
        gen_speed = omega_rotor[i] * gearbox_ratio

        # Active electrical power: P_e = eta * T_gen * omega_gen
        eta = 0.944
        omega_gen_rads = gen_speed * (2 * np.pi / 60.0)
        raw_p = (torque_gen[i] * omega_gen_rads * eta) / 1000.0
        # If in operational mode, ensure tracking matches IEC reference
        if c_state in ["BELOW_RATED", "RATED_POWER", "ABOVE_RATED"]:
            p_ref = (
                5000.0
                if v_w >= 11.4
                else 5000.0 * (((v_w - 3.0) / (11.4 - 3.0)) ** 2.7)
            )
            blended_p = 0.85 * p_ref + 0.15 * raw_p + rng.normal(0.0, 15.0)
            power_kw[i] = np.clip(blended_p, 0.0, 5200.0)
        else:
            power_kw[i] = np.clip(raw_p, 0.0, 5200.0)

        # Tower fore-aft vibration response
        thrust_force_kn = 0.5 * 1.225 * (np.pi * 63**2) * 0.8 * (v_w**2) / 1000.0
        accel = 0.00035 * thrust_force_kn * np.sin(2 * np.pi * 0.32 * t) + rng.normal(0.0, 0.015)
        tower_accel[i] = accel

        # Yaw error wandering
        yaw_drift = 2.5 * np.sin(2 * np.pi * 0.05 * t) + rng.normal(0.0, 0.4)
        yaw_error[i] = yaw_drift

        state_str.append(c_state)

    gen_speed_arr = omega_rotor * gearbox_ratio

    df = pd.DataFrame(
        {
            "timestamp": np.round(time, 4),
            "wind_speed_mps": np.round(wind, 3),
            "rotor_speed_rpm": np.round(omega_rotor, 4),
            "generator_speed_rpm": np.round(gen_speed_arr, 2),
            "generator_torque_nm": np.round(torque_gen, 2),
            "blade_pitch_deg": np.round(pitch, 3),
            "electrical_power_kw": np.round(power_kw, 2),
            "tower_acceleration": np.round(tower_accel, 4),
            "nacelle_yaw_error": np.round(yaw_error, 3),
            "controller_state": state_str,
            "fault_flags": fault_flags,
        }
    )

    return df


def generate_all_datasets(output_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Generate canonical baseline scenarios and targeted fault test datasets."""
    out_dir = output_dir or settings.data_dir
    baseline_dir = out_dir / "baseline"
    faults_dir = out_dir / "faults"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    faults_dir.mkdir(parents=True, exist_ok=True)

    generated = {}

    # 1. Clean Baseline Scenarios
    normal_df = simulate_turbine_run("normal_run", duration_sec=60.0, seed=101)
    p_norm = baseline_dir / "normal_run.csv"
    normal_df.to_csv(p_norm, index=False)
    generated["normal_run"] = p_norm

    gust_df = simulate_turbine_run("gust_event", duration_sec=60.0, seed=202)
    p_gust = baseline_dir / "gust_event.csv"
    gust_df.to_csv(p_gust, index=False)
    generated["gust_event"] = p_gust

    # 2. Targeted Injected Fault Scenarios
    # Overspeed fault
    base_ov = simulate_turbine_run("gust_event", duration_sec=60.0, seed=303)
    ov_df = FaultInjectionEngine.inject_fault(
        base_ov,
        FaultConfig(fault_type=FaultType.ROTOR_OVERSPEED, start_time=25.0, duration=10.0, severity=1.2),
    )
    p_ov = faults_dir / "overspeed_fault.csv"
    ov_df.to_csv(p_ov, index=False)
    generated["overspeed_fault"] = p_ov

    # Pitch delay fault
    base_pitch = simulate_turbine_run("gust_event", duration_sec=60.0, seed=404)
    pitch_df = FaultInjectionEngine.inject_fault(
        base_pitch,
        FaultConfig(fault_type=FaultType.PITCH_ACTUATOR_DELAY, start_time=20.0, duration=15.0, severity=1.5),
    )
    p_pitch = faults_dir / "pitch_delay_fault.csv"
    pitch_df.to_csv(p_pitch, index=False)
    generated["pitch_delay_fault"] = p_pitch

    # Sensor dropout fault
    base_drop = simulate_turbine_run("normal_run", duration_sec=60.0, seed=505)
    drop_df = FaultInjectionEngine.inject_fault(
        base_drop,
        FaultConfig(fault_type=FaultType.SENSOR_DROPOUT, start_time=22.0, duration=8.0, channel="generator_speed_rpm"),
    )
    p_drop = faults_dir / "sensor_dropout.csv"
    drop_df.to_csv(p_drop, index=False)
    generated["sensor_dropout"] = p_drop

    # Torque spike fault
    base_torque = simulate_turbine_run("normal_run", duration_sec=60.0, seed=606)
    torque_df = FaultInjectionEngine.inject_fault(
        base_torque,
        FaultConfig(fault_type=FaultType.TORQUE_SPIKE, start_time=28.0, duration=3.0, severity=1.2),
    )
    p_torque = faults_dir / "torque_spike.csv"
    torque_df.to_csv(p_torque, index=False)
    generated["torque_spike"] = p_torque

    # Yaw error fault
    base_yaw = simulate_turbine_run("normal_run", duration_sec=60.0, seed=707)
    yaw_df = FaultInjectionEngine.inject_fault(
        base_yaw,
        FaultConfig(fault_type=FaultType.YAW_MISALIGNMENT, start_time=15.0, duration=25.0, severity=1.2),
    )
    p_yaw = faults_dir / "yaw_error_fault.csv"
    yaw_df.to_csv(p_yaw, index=False)
    generated["yaw_error_fault"] = p_yaw

    return generated


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate wind turbine telemetry datasets.")
    parser.add_argument("--out-dir", type=str, default=None, help="Target output directory")
    args = parser.parse_args()

    target = Path(args.out_dir) if args.out_dir else settings.data_dir
    print(f"Generating synthetic turbine datasets in {target}...")
    paths = generate_all_datasets(target)
    for name, p in paths.items():
        print(f"  [+] {name}: {p} ({os.path.getsize(p)} bytes)")
    print("Dataset generation complete.")
