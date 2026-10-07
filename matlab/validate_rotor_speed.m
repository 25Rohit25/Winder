function speed_metrics = validate_rotor_speed(csv_filepath)
% VALIDATE_ROTOR_SPEED Evaluates rotor angular speed and FFT frequency harmonics.
%
% Computes peak speed, operational range violations, and spectral 1P / 3P content.

    if nargin < 1
        csv_filepath = fullfile('..', 'data', 'baseline', 'normal_run.csv');
    end

    data = readtable(csv_filepath);
    time = data.timestamp;
    rotor_rpm = data.rotor_speed_rpm;

    dt = mean(diff(time));
    fs = 1.0 / dt;

    min_rpm = min(rotor_rpm);
    max_rpm = max(rotor_rpm);
    mean_rpm = mean(rotor_rpm);

    % Fast Fourier Transform (FFT) for Harmonic Analysis
    N = length(rotor_rpm);
    f = (0:(N/2)) * (fs / N);
    rpm_zero_mean = rotor_rpm - mean_rpm;
    Y = fft(rpm_zero_mean);
    P2 = abs(Y / N);
    P1 = P2(1:floor(N/2)+1);
    P1(2:end-1) = 2 * P1(2:end-1);

    % Dominant rotational frequency
    [~, max_freq_idx] = max(P1(2:end));
    dom_freq_hz = f(max_freq_idx + 1);

    speed_metrics = struct();
    speed_metrics.min_rpm = min_rpm;
    speed_metrics.max_rpm = max_rpm;
    speed_metrics.mean_rpm = mean_rpm;
    speed_metrics.dominant_frequency_hz = dom_freq_hz;
    speed_metrics.overspeed_trip = max_rpm > 15.00;

    fprintf('Rotor Speed: Min=%.2f, Max=%.2f, Mean=%.2f RPM | Dom Freq=%.3f Hz\n', ...
        min_rpm, max_rpm, mean_rpm, dom_freq_hz);
end
