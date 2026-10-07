function faulted_data = inject_faults(csv_filepath, fault_type, start_time, duration, severity)
% INJECT_FAULTS Inject controlled synthetic fault anomalies into turbine telemetry.
%
% Syntax:
%   faulted_data = inject_faults('data/baseline/normal_run.csv', 'ROTOR_OVERSPEED', 20.0, 10.0, 1.2)
%
% Fault Types Supported:
%   'ROTOR_OVERSPEED'       - Over-accelerates rotor past 15.0 RPM trip
%   'PITCH_ACTUATOR_DELAY'  - Freezes blade pitch shedding above rated wind
%   'SENSOR_DROPOUT'        - Injects NaN dropouts on generator speed
%   'TORQUE_SPIKE'          - Steps generator torque above peak limit

    if nargin < 5, severity = 1.0; end
    if nargin < 4, duration = 10.0; end
    if nargin < 3, start_time = 20.0; end
    if nargin < 2, fault_type = 'ROTOR_OVERSPEED'; end
    if nargin < 1, csv_filepath = fullfile('..', 'data', 'baseline', 'normal_run.csv'); end

    data = readtable(csv_filepath);
    mask = (data.timestamp >= start_time) & (data.timestamp <= (start_time + duration));

    switch upper(fault_type)
        case 'ROTOR_OVERSPEED'
            data.rotor_speed_rpm(mask) = data.rotor_speed_rpm(mask) + (2.5 * severity);
            data.generator_speed_rpm(mask) = data.rotor_speed_rpm(mask) * 97.0;

        case 'PITCH_ACTUATOR_DELAY'
            data.blade_pitch_deg(mask) = max(0.0, data.blade_pitch_deg(mask) - (5.0 * severity));

        case 'SENSOR_DROPOUT'
            data.generator_speed_rpm(mask) = NaN;

        case 'TORQUE_SPIKE'
            data.generator_torque_nm(mask) = data.generator_torque_nm(mask) + (14000.0 * severity);

        otherwise
            error('Unknown fault type: %s', fault_type);
    end

    % Set fault flag bit
    data.fault_flags(mask) = bitor(data.fault_flags(mask), 1);
    faulted_data = data;
    fprintf('Fault injection [%s] applied from %.1fs to %.1fs (severity: %.2f).\n', ...
        fault_type, start_time, start_time + duration, severity);
end
