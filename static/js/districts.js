
// Logic to handle states and districts
// Requires INDIAN_STATES_DATA to be loaded from indian_states_districts.js

// Transform downloaded data to map format for easier lookup
// Format: { "STATE NAME": ["District 1", "District 2"] }
const stateDistrictsMap = {};

// Fallback data if external fails (minimal set to ensure UI doesn't look broken)
const FALLBACK_DATA = {
    "MAHARASHTRA": ["Ahmednagar", "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik", "Osmanabad", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal"],
    "KARNATAKA": ["Bengaluru Urban", "Belagavi", "Mysuru"],
    "GUJARAT": ["Ahmedabad", "Surat", "Vadodara"]
};

try {
    const data = window.INDIAN_STATES_DATA || (typeof INDIAN_STATES_DATA !== 'undefined' ? INDIAN_STATES_DATA : null);

    if (data && data.states) {
        // console.log("Loading Indian States Data...");
        data.states.forEach(stateObj => {
            // Upper case state name to match typical dropdown values
            const stateName = stateObj.state.toUpperCase().trim();
            stateDistrictsMap[stateName] = stateObj.districts;
        });
        // console.log("Loaded " + Object.keys(stateDistrictsMap).length + " states.");
    } else {
        console.error("INDIAN_STATES_DATA not found. Using Fallback.");
        Object.assign(stateDistrictsMap, FALLBACK_DATA);
    }
} catch (e) {
    console.error("Error processing Indian States Data", e);
    Object.assign(stateDistrictsMap, FALLBACK_DATA);
}

// Backward compatibility references
const districtData = stateDistrictsMap;
const stateDistricts = stateDistrictsMap;

/**
 * Populate a State Select Element with options
 * @param {string} elementId - ID of the select element
 * @param {string} selectedValue - Value to select
 */
function populateStates(elementId, selectedValue = null) {
    const select = document.getElementById(elementId);
    if (!select) {
        console.warn("State select element not found: " + elementId);
        return;
    }

    // Keep the first option (usually "Select State")
    // If empty or just placeholder, clear it (except first)
    // But careful not to duplicate if called multiple times

    // Simplest approach: Clear all except first
    const firstOption = select.options[0];
    select.innerHTML = '';
    if (firstOption) select.appendChild(firstOption);
    else {
        const opt = document.createElement('option');
        opt.value = "";
        opt.textContent = "Select State";
        select.appendChild(opt);
    }

    const states = Object.keys(stateDistrictsMap).sort();

    states.forEach(state => {
        const option = document.createElement('option');
        option.value = state;
        option.textContent = state;
        if (selectedValue && state === selectedValue.toUpperCase()) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

/**
 * Populate a District Select Element based on selected State
 * @param {string} stateElementId - ID of the state select element
 * @param {string} districtElementId - ID of the district select element
 * @param {string} selectedDistrict - Value to select
 */
function populateDistricts(stateElementId, districtElementId, selectedDistrict = null) {
    const stateSelect = document.getElementById(stateElementId);
    const districtSelect = document.getElementById(districtElementId);

    // Support single argument legacy call if only district ID passed (though we updated calls)
    // Actually, legacy call is verify tricky. Let's stick to explicit args.

    if (!stateSelect || !districtSelect) return;

    const selectedState = stateSelect.value;

    // Clear existing districts
    districtSelect.innerHTML = '<option value="">Select District</option>';

    if (selectedState && stateDistrictsMap[selectedState]) {
        stateDistrictsMap[selectedState].forEach(district => {
            const option = document.createElement('option');
            option.value = district;
            option.textContent = district;
            if (district === selectedDistrict) {
                option.selected = true;
            }
            districtSelect.appendChild(option);
        });
    }
}

// Helper to init both for a page
function initLocationDropdowns(stateId, districtId, defaultState = null, defaultDistrict = null) {
    populateStates(stateId, defaultState);

    const stateSelect = document.getElementById(stateId);
    if (stateSelect) {
        stateSelect.addEventListener('change', () => {
            populateDistricts(stateId, districtId);
        });

        // Trigger once to load districts if state is selected
        if (stateSelect.value) {
            populateDistricts(stateId, districtId, defaultDistrict);
        }
    }
}

// Global scope attachment for debugging
window.populateStates = populateStates;
window.populateDistricts = populateDistricts;
window.stateDistrictsMap = stateDistrictsMap;
