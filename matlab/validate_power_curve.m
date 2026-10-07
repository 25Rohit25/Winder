function stats = validate_power_curve(csv_filepath)
% VALIDATE_POWER_CURVE IEC 61400-12 binned wind turbine power curve validator.
%
% Calculates bin-averaged electrical power, standard deviations, and compares
% against NREL 5MW baseline reference characteristic curve.

    if nargin < 1
        csv_filepath = fullfile('..', 'data', 'baseline', 'normal_run.csv');
    end

    data = readtable(csv_filepath);
    wind = data.wind_speed_mps;
    power = data.electrical_power_kw;

    bin_width = 1.0;
    v_bins = 3.0:bin_width:25.0;
    num_bins = length(v_bins) - 1;

    bin_centers = zeros(num_bins, 1);
    bin_means = zeros(num_bins, 1);
    bin_stds = zeros(num_bins, 1);
    ref_curve = zeros(num_bins, 1);
    dev_pct = zeros(num_bins, 1);

    for i = 1:num_bins
        v_low = v_bins(i);
        v_high = v_bins(i+1);
        v_mid = (v_low + v_high) / 2.0;
        bin_centers(i) = v_mid;

        idx = (wind >= v_low) & (wind < v_high);
        if any(idx)
            bin_means(i) = mean(power(idx));
            bin_stds(i) = std(power(idx));
        else
            bin_means(i) = NaN;
            bin_stds(i) = NaN;
        end

        % Reference NREL 5MW Power (kW)
        if v_mid >= 11.4
            ref_curve(i) = 5000.0;
        else
            ref_curve(i) = 5000.0 * (((v_mid - 3.0) / (11.4 - 3.0))^2.7);
        end

        if ~isnan(bin_means(i))
            dev_pct(i) = abs(bin_means(i) - ref_curve(i)) / 5000.0 * 100.0;
        else
            dev_pct(i) = NaN;
        end
    end

    max_dev = max(dev_pct(~isnan(dev_pct)));
    if isempty(max_dev)
        max_dev = 0.0;
    end

    stats = struct();
    stats.bin_centers = bin_centers;
    stats.bin_means_kw = bin_means;
    stats.bin_stds_kw = bin_stds;
    stats.ref_curve_kw = ref_curve;
    stats.max_deviation_pct = max_dev;
    stats.passed = max_dev <= 10.0;

    fprintf('Power Curve IEC Bin Analysis: Max deviation = %.2f%% (Pass threshold <= 10.0%%)\n', max_dev);
end
