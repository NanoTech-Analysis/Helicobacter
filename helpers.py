class ExpectedPeak:
    def __init__(
            self,
            nominal_mass,
            is_main = False,
            mass_margin_left=0.4,
            mass_margin_right=0.4,
    ):
        self.nominal_mass = nominal_mass
        self.is_main = is_main
        self.mass_margin_left = mass_margin_left
        self.mass_margin_right = mass_margin_right


class Compound:
    def __init__(
            self,
            name,
            expected_peaks_list,
            peaks_ratios_list = []
    ):
        self.name = name
        self.expected_peaks = expected_peaks_list
        self.main_peak = list(peak for peak in expected_peaks_list if peak.is_main)[0]
        self.peaks_ratios_list = peaks_ratios_list