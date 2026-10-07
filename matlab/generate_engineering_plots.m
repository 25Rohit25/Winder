function generate_engineering_plots(csv_filepath, output_dir)
% GENERATE_ENGINEERING_PLOTS Produces 6-panel validation figures from telemetry data.
%
% Syntax:
%   generate_engineering_plots('data/baseline/normal_run.csv', 'reports/generated')

    if nargin < 2
        output_dir = fullfile('..', 'reports', 'generated');
    end
    if nargin < 1
        csv_filepath = fullfile('..', 'data', 'baseline', 'normal_run.csv');
    end

    if ~exist(output_dir, 'dir')
        mkdir(output_dir);
    end

    data = readtable(csv_filepath);
    time = data.timestamp;

    fig = figure('Visible', 'off', 'Position', [100, 100, 1200, 800]);

    % Subplot 1: Wind Speed vs Time
    subplot(3, 2, 1);
    plot(time, data.wind_speed_mps, 'Color', [0.1, 0.4, 0.8], 'LineWidth', 1.5);
    yline(11.4, '--r', 'Rated (11.4 m/s)');
    grid on;
    xlabel('Time (s)'); ylabel('Wind Speed (m/s)');
    title('Hub-Height Wind Speed Telemetry');

    % Subplot 2: Rotor & Generator Speed vs Time
    subplot(3, 2, 2);
    yyaxis left;
    plot(time, data.rotor_speed_rpm, 'Color', [0.2, 0.7, 0.3], 'LineWidth', 1.5);
    yline(15.0, '--r', 'Trip Limit (15.0 RPM)');
    ylabel('Rotor Speed (RPM)');
    yyaxis right;
    plot(time, data.generator_speed_rpm, 'Color', [0.8, 0.5, 0.1], 'LineWidth', 1.0);
    ylabel('Generator Speed (RPM)');
    grid on; xlabel('Time (s)');
    title('Drivetrain Kinematics');

    % Subplot 3: Blade Pitch Angle
    subplot(3, 2, 3);
    plot(time, data.blade_pitch_deg, 'Color', [0.6, 0.2, 0.7], 'LineWidth', 1.5);
    grid on; xlabel('Time (s)'); ylabel('Pitch Angle (deg)');
    title('Collective Blade Pitch Control Response');

    % Subplot 4: Generator Torque vs Time
    subplot(3, 2, 4);
    plot(time, data.generator_torque_nm / 1000.0, 'Color', [0.9, 0.3, 0.2], 'LineWidth', 1.5);
    yline(43.09, '--k', 'Rated (43.09 kNm)');
    grid on; xlabel('Time (s)'); ylabel('Torque (kNm)');
    title('Generator Electromagnetic Torque Demand');

    % Subplot 5: Power vs Wind Speed (Power Curve)
    subplot(3, 2, 5);
    scatter(data.wind_speed_mps, data.electrical_power_kw, 15, [0.3, 0.5, 0.7], 'filled');
    grid on; xlabel('Wind Speed (m/s)'); ylabel('Power (kW)');
    yline(5000, '--r', 'Rated Capacity (5000 kW)');
    title('IEC 61400-12 Measured Power Curve');

    % Subplot 6: Nacelle Yaw Error
    subplot(3, 2, 6);
    plot(time, data.nacelle_yaw_error, 'Color', [0.1, 0.7, 0.7], 'LineWidth', 1.5);
    yline(10.0, '--r', 'Yaw Tolerance (+10 deg)');
    yline(-10.0, '--r', 'Yaw Tolerance (-10 deg)');
    grid on; xlabel('Time (s)'); ylabel('Yaw Error (deg)');
    title('Nacelle Wind Alignment Tracking');

    sgtitle('WindCtrl Validate - Turbine Dynamic Telemetry Review', 'FontSize', 14, 'FontWeight', 'bold');

    out_file = fullfile(output_dir, 'matlab_validation_telemetry.png');
    saveas(fig, out_file);
    close(fig);
    fprintf('Exported engineering telemetry plot to: %s\n', out_file);
end
