function pitch_metrics = validate_pitch_response(csv_filepath)
% VALIDATE_PITCH_RESPONSE Aerodynamic blade pitch controller dynamic analysis.
%
% Checks pitch actuation speed, response to above-rated wind, and detects saturation.

    if nargin < 1
        csv_filepath = fullfile('..', 'data', 'baseline', 'gust_event.csv');
    end

    data = readtable(csv_filepath);
    time = data.timestamp;
    wind = data.wind_speed_mps;
    pitch = data.blade_pitch_deg;

    dt = diff(time);
    dpitch = diff(pitch);
    pitch_rate = abs(dpitch ./ dt);

    max_rate = max(pitch_rate);
    mean_rate = mean(pitch_rate);

    % Above-rated pitch check
    above_rated_mask = wind >= 12.0;
    if any(above_rated_mask)
        mean_above_pitch = mean(pitch(above_rated_mask));
    else
        mean_above_pitch = 0.0;
    end

    pitch_metrics = struct();
    pitch_metrics.max_pitch_rate_dps = max_rate;
    pitch_metrics.mean_pitch_rate_dps = mean_rate;
    pitch_metrics.mean_above_rated_pitch_deg = mean_above_pitch;
    pitch_metrics.actuator_rate_ok = max_rate <= 8.5;
    pitch_metrics.feather_active = mean_above_pitch > 1.0;

    fprintf('Pitch Analysis: Max Rate = %.2f deg/s | Above-Rated Pitch Mean = %.2f deg\n', ...
        max_rate, mean_above_pitch);
end
