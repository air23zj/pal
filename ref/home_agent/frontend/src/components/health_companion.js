import { health } from '../utils/health-api';
import { showLoading, showError, showSuccess, formatDate } from '../utils/ui';
import { loadMainContent } from '../main.js';

export function loadHealthCompanionInterface() {
    const mainContent = document.getElementById('mainContent');
    if (!mainContent) return;

    mainContent.innerHTML = `
        <div class="max-w-6xl mx-auto px-4 py-6">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-2xl font-bold text-gray-900">Health Companion</h2>
                <button id="backButton" class="text-gray-600 hover:text-gray-800">
                    <i class="fas fa-arrow-left mr-2"></i>Back to Home
                </button>
            </div>
            
            <!-- Health Dashboard -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <!-- Weight & Height Card -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <h3 class="text-lg font-semibold mb-4">Body Measurements</h3>
                    <div class="space-y-4">
                        <!-- Weight -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Weight (kg)</label>
                            <div class="flex items-center gap-2">
                                <input type="number" id="weightInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Weight in kg">
                                <button id="saveWeightBtn" class="bg-primary-600 text-white px-3 py-2 rounded-md hover:bg-primary-700">Save</button>
                            </div>
                            <div id="weightHistory" class="mt-2 text-sm text-gray-600"></div>
                        </div>
                        <!-- Height -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Height (cm)</label>
                            <div class="flex items-center gap-2">
                                <input type="number" id="heightInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Height in cm">
                                <button id="saveHeightBtn" class="bg-primary-600 text-white px-3 py-2 rounded-md hover:bg-primary-700">Save</button>
                            </div>
                            <div id="heightHistory" class="mt-2 text-sm text-gray-600"></div>
                        </div>
                    </div>
                </div>

                <!-- Heart Rate & Blood Pressure Card -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <h3 class="text-lg font-semibold mb-4">Vital Signs</h3>
                    <div class="space-y-4">
                        <!-- Heart Rate -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Heart Rate (bpm)</label>
                            <div class="flex items-center gap-2">
                                <input type="number" id="heartRateInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Heart rate">
                                <select id="activityState" class="mt-1 block rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500">
                                    <option value="resting">Resting</option>
                                    <option value="active">Active</option>
                                </select>
                                <button id="saveHeartRateBtn" class="bg-primary-600 text-white px-3 py-2 rounded-md hover:bg-primary-700">Save</button>
                            </div>
                            <div id="heartRateHistory" class="mt-2 text-sm text-gray-600"></div>
                        </div>
                        <!-- Blood Pressure -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Blood Pressure (mmHg)</label>
                            <div class="flex items-center gap-2">
                                <input type="number" id="systolicInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Systolic">
                                <input type="number" id="diastolicInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Diastolic">
                                <button id="saveBloodPressureBtn" class="bg-primary-600 text-white px-3 py-2 rounded-md hover:bg-primary-700">Save</button>
                            </div>
                            <div id="bloodPressureHistory" class="mt-2 text-sm text-gray-600"></div>
                        </div>
                    </div>
                </div>

                <!-- Doctor Visits Card -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <h3 class="text-lg font-semibold mb-4">Doctor Visits</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Doctor Name</label>
                            <input type="text" id="doctorNameInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Doctor's name">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Reason</label>
                            <input type="text" id="visitReasonInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Reason for visit">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Notes</label>
                            <textarea id="visitNotesInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" rows="2" placeholder="Visit notes"></textarea>
                        </div>
                        <button id="saveDoctorVisitBtn" class="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                            Save Visit
                        </button>
                        <div id="doctorVisitsHistory" class="mt-2 text-sm text-gray-600"></div>
                    </div>
                </div>

                <!-- Exercise Goals Card -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <h3 class="text-lg font-semibold mb-4">Exercise Goals</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Daily Steps Goal</label>
                            <input type="number" id="stepsGoalInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Target steps">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Weekly Exercise Minutes</label>
                            <input type="number" id="exerciseMinutesInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Minutes per week">
                        </div>
                        <button id="saveExerciseGoalsBtn" class="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                            Save Exercise Goals
                        </button>
                    </div>
                </div>

                <!-- Dietary Goals Card -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <h3 class="text-lg font-semibold mb-4">Dietary Goals</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Daily Calories Goal</label>
                            <input type="number" id="caloriesGoalInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Target calories">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Daily Water Intake (L)</label>
                            <input type="number" id="waterIntakeInput" class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500" placeholder="Target water intake">
                        </div>
                        <button id="saveDietaryGoalsBtn" class="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700">
                            Save Dietary Goals
                        </button>
                    </div>
                </div>

                <!-- Health Recommendations Card -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <h3 class="text-lg font-semibold mb-4">Recommendations</h3>
                    <div id="recommendationsContainer" class="space-y-4">
                        <!-- Recommendations will be dynamically inserted here -->
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add event listeners
    const backButton = document.getElementById('backButton');
    backButton.addEventListener('click', () => {
        history.pushState(null, '', '/');
        loadMainContent();
    });

    // Weight
    document.getElementById('saveWeightBtn').addEventListener('click', async () => {
        const weight = document.getElementById('weightInput').value;
        try {
            await health.saveWeight({ weight: parseFloat(weight) });
            loadWeightHistory();
            showSuccess('Weight saved successfully');
        } catch (error) {
            showError('Failed to save weight');
        }
    });

    // Height
    document.getElementById('saveHeightBtn').addEventListener('click', async () => {
        const height = document.getElementById('heightInput').value;
        try {
            await health.saveHeight({ height: parseFloat(height) });
            loadHeightHistory();
            showSuccess('Height saved successfully');
        } catch (error) {
            showError('Failed to save height');
        }
    });

    // Heart Rate
    document.getElementById('saveHeartRateBtn').addEventListener('click', async () => {
        const heartRate = document.getElementById('heartRateInput').value;
        const activityState = document.getElementById('activityState').value;
        try {
            await health.saveHeartRate({ 
                heart_rate: parseInt(heartRate),
                activity_state: activityState
            });
            loadHeartRateHistory();
            showSuccess('Heart rate saved successfully');
        } catch (error) {
            showError('Failed to save heart rate');
        }
    });

    // Blood Pressure
    document.getElementById('saveBloodPressureBtn').addEventListener('click', async () => {
        const systolic = document.getElementById('systolicInput').value;
        const diastolic = document.getElementById('diastolicInput').value;
        try {
            await health.saveBloodPressure({
                systolic: parseInt(systolic),
                diastolic: parseInt(diastolic)
            });
            loadBloodPressureHistory();
            showSuccess('Blood pressure saved successfully');
        } catch (error) {
            showError('Failed to save blood pressure');
        }
    });

    // Doctor Visit
    document.getElementById('saveDoctorVisitBtn').addEventListener('click', async () => {
        const doctorName = document.getElementById('doctorNameInput').value;
        const reason = document.getElementById('visitReasonInput').value;
        const notes = document.getElementById('visitNotesInput').value;
        try {
            await health.saveDoctorVisit({
                doctor_name: doctorName,
                reason: reason,
                notes: notes
            });
            loadDoctorVisits();
            showSuccess('Doctor visit saved successfully');
        } catch (error) {
            showError('Failed to save doctor visit');
        }
    });

    // Exercise Goals
    document.getElementById('saveExerciseGoalsBtn').addEventListener('click', async () => {
        const dailySteps = document.getElementById('stepsGoalInput').value;
        const weeklyExerciseMinutes = document.getElementById('exerciseMinutesInput').value;
        try {
            await health.saveExerciseGoals({
                dailySteps: parseInt(dailySteps),
                weeklyExerciseMinutes: parseInt(weeklyExerciseMinutes)
            });
            showSuccess('Exercise goals saved successfully');
        } catch (error) {
            showError('Failed to save exercise goals');
        }
    });

    // Dietary Goals
    document.getElementById('saveDietaryGoalsBtn').addEventListener('click', async () => {
        const dailyCalories = document.getElementById('caloriesGoalInput').value;
        const waterIntake = document.getElementById('waterIntakeInput').value;
        try {
            await health.saveDietaryGoals({
                dailyCalories: parseInt(dailyCalories),
                waterIntake: parseFloat(waterIntake)
            });
            showSuccess('Dietary goals saved successfully');
        } catch (error) {
            showError('Failed to save dietary goals');
        }
    });

    // Load initial data
    loadWeightHistory();
    loadHeightHistory();
    loadHeartRateHistory();
    loadBloodPressureHistory();
    loadDoctorVisits();
    loadExerciseGoals();
    loadDietaryGoals();
    loadRecommendations();
}

async function loadWeightHistory() {
    try {
        const weightData = await health.getWeightHistory();
        const weightHistory = document.getElementById('weightHistory');
        weightHistory.innerHTML = weightData.map(entry => `
            <div class="flex justify-between">
                <span>${formatDate(entry.date)}</span>
                <span>${entry.weight} kg</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading weight history:', error);
        showError('Failed to load weight history');
    }
}

async function loadHeightHistory() {
    try {
        const heightData = await health.getHeightHistory();
        const heightHistory = document.getElementById('heightHistory');
        heightHistory.innerHTML = heightData.map(entry => `
            <div class="flex justify-between">
                <span>${formatDate(entry.date)}</span>
                <span>${entry.height} cm</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading height history:', error);
        showError('Failed to load height history');
    }
}

async function loadHeartRateHistory() {
    try {
        const heartRateData = await health.getHeartRateHistory();
        const heartRateHistory = document.getElementById('heartRateHistory');
        heartRateHistory.innerHTML = heartRateData.map(entry => `
            <div class="flex justify-between">
                <span>${formatDate(entry.date)}</span>
                <span>${entry.heart_rate} bpm (${entry.activity_state})</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading heart rate history:', error);
        showError('Failed to load heart rate history');
    }
}

async function loadBloodPressureHistory() {
    try {
        const bpData = await health.getBloodPressureHistory();
        const bpHistory = document.getElementById('bloodPressureHistory');
        bpHistory.innerHTML = bpData.map(entry => `
            <div class="flex justify-between">
                <span>${formatDate(entry.date)}</span>
                <span>${entry.systolic}/${entry.diastolic} mmHg</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading blood pressure history:', error);
        showError('Failed to load blood pressure history');
    }
}

async function loadDoctorVisits() {
    try {
        const visits = await health.getDoctorVisits();
        const visitsHistory = document.getElementById('doctorVisitsHistory');
        visitsHistory.innerHTML = visits.map(visit => `
            <div class="border-t border-gray-200 pt-2 mt-2">
                <div class="font-medium">${visit.doctor_name}</div>
                <div class="text-gray-600">${formatDate(visit.date)}</div>
                <div class="text-gray-800">${visit.reason}</div>
                ${visit.notes ? `<div class="text-gray-600 text-sm">${visit.notes}</div>` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading doctor visits:', error);
        showError('Failed to load doctor visits');
    }
}

async function loadExerciseGoals() {
    try {
        const goals = await health.getExerciseGoals();
        document.getElementById('stepsGoalInput').value = goals.dailySteps;
        document.getElementById('exerciseMinutesInput').value = goals.weeklyExerciseMinutes;
    } catch (error) {
        console.error('Error loading exercise goals:', error);
        showError('Failed to load exercise goals');
    }
}

async function loadDietaryGoals() {
    try {
        const goals = await health.getDietaryGoals();
        document.getElementById('caloriesGoalInput').value = goals.dailyCalories;
        document.getElementById('waterIntakeInput').value = goals.waterIntake;
    } catch (error) {
        console.error('Error loading dietary goals:', error);
        showError('Failed to load dietary goals');
    }
}

async function loadRecommendations() {
    try {
        // First, gather all health data to generate personalized recommendations
        const [weightData, heightData, heartRateData, bpData, exerciseGoals, dietaryGoals] = await Promise.all([
            health.getWeightHistory(),
            health.getHeightHistory(),
            health.getHeartRateHistory(),
            health.getBloodPressureHistory(),
            health.getExerciseGoals(),
            health.getDietaryGoals()
        ]);

        // Get the most recent measurements
        const latestWeight = weightData[0]?.weight;
        const latestHeight = heightData[0]?.height;
        const latestHeartRate = heartRateData[0]?.heart_rate;
        const latestBP = bpData[0];

        // Calculate BMI if both weight and height are available
        let bmi;
        if (latestWeight && latestHeight) {
            bmi = (latestWeight / Math.pow(latestHeight / 100, 2)).toFixed(1);
        }

        // Prepare health data summary for LLM
        const healthSummary = {
            measurements: {
                bmi: bmi,
                weight: latestWeight,
                height: latestHeight,
                heartRate: latestHeartRate,
                bloodPressure: latestBP ? `${latestBP.systolic}/${latestBP.diastolic}` : null
            },
            goals: {
                dailySteps: exerciseGoals?.dailySteps,
                weeklyExerciseMinutes: exerciseGoals?.weeklyExerciseMinutes,
                dailyCalories: dietaryGoals?.dailyCalories,
                waterIntake: dietaryGoals?.waterIntake
            }
        };

        // Get personalized recommendations
        const recommendations = await health.getRecommendations(healthSummary);
        const container = document.getElementById('recommendationsContainer');
        container.innerHTML = recommendations.map(rec => `
            <div class="border-b border-gray-200 pb-4 last:border-b-0">
                <h4 class="font-medium text-gray-900">${rec.title}</h4>
                <p class="text-gray-600 text-sm mt-1">${rec.description}</p>
                <ul class="list-disc list-inside text-sm text-gray-600 mt-2">
                    ${rec.actionItems.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading recommendations:', error);
        showError('Failed to load recommendations');
    }
} 