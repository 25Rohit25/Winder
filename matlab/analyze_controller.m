function results = analyze_controller(csv_filepath)
% ANALYZE_CONTROLLER Master validation analysis script for wind turbine controllers.
%
% Syntax:
%   results = analyze_controller('data/baseline/normal_run.csv')
%
% Inputs:
%   csv_filepath - Path to 11-channel wind turbine telemetry CSV file.
%
% Outputs:
%   results - Struct containing calculated engineering metrics and validation verdicts.

    if nargin < 1
        csv_filepath = fullfile('..', 'data', 'baseline', 'normal_run.csv');
    end

    fprintf('=================================================================\n');
    fprintf(' WindCtrl Validate - MATLAB Controller Analysis Engine\n');
    fprintf(' Telemetry Input: %s\n', csv_filepath);
    fprintf('=================================================================\n\n');

    % Ingest Telemetry Table
    data = readtable(csv_filepath);
    time = data.timestamp;
    wind = data.wind_speed_mps;
    rotor_rpm = data.rotor_speed_rpm;
    gen_rpm = data.generator_speed_rpm;
    torque = data.generator_torque_nm;
    pitch = data.blade_pitch_deg;
    power = data.electrical_power_kw;
    yaw = data.nacelle_yaw_error;

    dt = mean(diff(time));
    duration = time(end) - time(1);

    % 1. Kinematic Checks
    max_rotor = max(rotor_rpm);
    overspeed_limit = 15.00;
    overspeed_pass = max_rotor <= overspeed_limit;

    % 2. Power Metrics
    max_power = max(power);
    rated_power = 5000.0;
    power_pass = max_power <= (rated_power * 1.10);

    % 3. Pitch Actuator Slew Rate
    pitch_rate = abs(diff(pitch) ./ diff(time));
    max_pitch_rate = max(pitch_rate);
    pitch_rate_pass = max_pitch_rate <= 8.5;

    % 4. Drivetrain Gearbox Ratio
    valid_idx = rotor_rpm > 1.0;
    gear_ratio = gen_rpm(valid_idx) ./ rotor_rpm(valid_idx);
    mean_ratio = mean(gear_ratio);
    gear_pass = abs(mean_ratio - 97.0) < 1.0;

    % Populate Results Struct
    results = struct();
    results.duration_sec = duration;
    results.dt_sec = dt;
    results.max_rotor_speed_rpm = max_rotor;
    results.max_electrical_power_kw = max_power;
    results.max_pitch_rate_dps = max_pitch_rate;
    results.mean_gearbox_ratio = mean_ratio;
    results.verdicts = struct(...
        'overspeed_pass', overspeed_pass, ...
        'power_overload_pass', power_pass, ...
        'pitch_rate_pass', pitch_rate_pass, ...
        'gearbox_pass', gear_pass ...
    );

    fprintf('Validation Summary:\n');
    fprintf('  Duration: %.2f s | dt: %.4f s\n', duration, dt);
    fprintf('  Max Rotor Speed: %.3f RPM [Limit: %.2f RPM] -> %s\n', ...
        max_rotor, overspeed_limit, status_str(overspeed_pass));
    fprintf('  Max Active Power: %.1f kW [Limit: %.1f kW] -> %s\n', ...
        max_power, rated_power*1.1, status_str(power_pass));
    fprintf('  Max Pitch Rate: %.2f deg/s [Limit: 8.5 deg/s] -> %s\n', ...
        max_pitch_rate, status_str(pitch_rate_pass));
    fprintf('  Gearbox Ratio: %.2f [Target: 97.0] -> %s\n', ...
        mean_ratio, status_str(gear_pass));
end

function s = status_str(flag)
    if flag
        s = 'PASS';
    else
        s = 'FAIL';
    end
end
