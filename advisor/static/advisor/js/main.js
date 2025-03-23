document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const searchForm = document.getElementById('search-form');
    const cityInput = document.getElementById('city-input');
    const countryInput = document.getElementById('country-input');
    const hobbyInput = document.getElementById('hobby-input');
    const resultsContainer = document.getElementById('results-container');
    const loadingElement = document.getElementById('loading');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const historyList = document.getElementById('history-list');
    const factDisplay = document.getElementById('travel-fact');
    
    // Session search history
    let searchHistory = [];
    let currentFactInterval;
    let factsEnabled = true;
    
    // Initialize sidebar toggle
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            mainContent.classList.toggle('sidebar-open');
            
            // Update icon
            if (sidebar.classList.contains('active')) {
                sidebarToggle.innerHTML = '&times;';
            } else {
                sidebarToggle.innerHTML = '&#9776;';
            }
        });
    }
    
    // Handle form submission
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const city = cityInput.value.trim();
            const country = countryInput.value.trim();
            const hobbies = hobbyInput.value.trim();
            
            if (city && country) {
                searchDestination(city, country, hobbies);
            }
        });
    }
    
    // Add event listeners to all section headers
    function initializeCollapsibleSections() {
        const sectionHeaders = document.querySelectorAll('.section-header');
        sectionHeaders.forEach(header => {
            header.addEventListener('click', function() {
                const content = this.nextElementSibling;
                const isActive = content.classList.contains('active');
                
                // Close all sections
                document.querySelectorAll('.section-content').forEach(section => {
                    section.classList.remove('active');
                });
                
                // Toggle the clicked section
                if (!isActive) {
                    content.classList.add('active');
                }
                
                // Update the arrow icon
                updateArrowIcons();
            });
        });
        
        // Open the first section by default
        const firstSection = document.querySelector('.section-content');
        if (firstSection) {
            firstSection.classList.add('active');
            updateArrowIcons();
        }
        
        // Initialize follow-up question handlers
        initializeFollowUpHandlers();
    }
    
    // Update arrow icons based on section state
    function updateArrowIcons() {
        const sectionHeaders = document.querySelectorAll('.section-header');
        sectionHeaders.forEach(header => {
            const content = header.nextElementSibling;
            const arrow = header.querySelector('.arrow');
            
            if (content.classList.contains('active')) {
                arrow.innerHTML = '&#9650;'; // Up arrow
            } else {
                arrow.innerHTML = '&#9660;'; // Down arrow
            }
        });
    }
    
    // Initialize follow-up question handlers
    function initializeFollowUpHandlers() {
        const followUpForms = document.querySelectorAll('.follow-up-form');
        followUpForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const inputField = this.querySelector('.follow-up-input-field');
                const followUpQuestion = inputField.value.trim();
                const destinationId = this.getAttribute('data-destination-id');
                
                if (followUpQuestion && destinationId) {
                    submitFollowUpQuestion(destinationId, followUpQuestion);
                    inputField.value = '';
                }
            });
        });
    }
    
    // Submit a follow-up question
    async function submitFollowUpQuestion(destinationId, question) {
        try {
            showLoading();
            
            // Get the existing destination data
            const destination = await getTravelAdvice(destinationId);
            
            // Construct a prompt that includes the follow-up question
            const prompt = `Follow-up question about ${destination.name}, ${destination.country}: ${question}`;
            
            // Call the API to generate advice based on the follow-up
            const response = await fetch(`/api/destinations/${destinationId}/generate_advice/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    follow_up_question: prompt
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to process follow-up question');
            }
            
            // Get the updated advice
            const updatedData = await getTravelAdvice(destinationId);
            
            // Display the results
            displayResults(updatedData, destination.name, destination.country);
            
            hideLoading();
        } catch (error) {
            console.error('Error:', error);
            showError('An error occurred while processing your follow-up question. Please try again.');
            hideLoading();
        }
    }
    
    // Search for destination and get travel advice
    async function searchDestination(city, country, hobbies = '') {
        try {
            showLoading();
            startFactsInterval();
            
            // Step 1: Check if the destination already exists or create a new one
            let destinationId = await getOrCreateDestination(city, country);
            
            // Step 2: Generate travel advice for the destination
            await generateAdvice(destinationId, hobbies);
            
            // Step 3: Get the travel advice details
            let adviceData = await getTravelAdvice(destinationId);
            
            // Step 4: Display the results
            displayResults(adviceData, city, country);
            
            // Step 5: Add to search history
            addToSearchHistory(adviceData);
            
            hideLoading();
            stopFactsInterval();
        } catch (error) {
            console.error('Error:', error);
            showError('An error occurred while getting travel advice. Please try again.');
            hideLoading();
            stopFactsInterval();
        }
    }
    
    // Add search to history
    function addToSearchHistory(data) {
        // Check if already in history
        const exists = searchHistory.some(item => item.id === data.id);
        
        if (!exists) {
            // Add to history array
            searchHistory.push(data);
            
            // Update the sidebar
            updateSearchHistorySidebar();
        }
    }
    
    // Update the search history sidebar
    function updateSearchHistorySidebar() {
        if (historyList) {
            // Clear current list
            historyList.innerHTML = '';
            
            // Add each history item
            searchHistory.forEach(item => {
                const historyItem = document.createElement('li');
                historyItem.className = 'history-item';
                historyItem.innerHTML = `
                    <h3>${item.name}, ${item.country}</h3>
                    <p>Last viewed: ${new Date().toLocaleTimeString()}</p>
                `;
                
                // Add click event to load this destination
                historyItem.addEventListener('click', function() {
                    displayResults(item, item.name, item.country);
                    
                    // Close sidebar on mobile
                    if (window.innerWidth < 768 && sidebar && sidebar.classList.contains('active')) {
                        sidebar.classList.remove('active');
                        mainContent.classList.remove('sidebar-open');
                        sidebarToggle.innerHTML = '&#9776;';
                    }
                });
                
                historyList.appendChild(historyItem);
            });
        }
    }
    
    // Display random travel facts during loading
    function startFactsInterval() {
        if (factsEnabled && factDisplay) {
            // Show initial fact
            displayRandomFact();
            
            // Change fact every 8 seconds
            currentFactInterval = setInterval(displayRandomFact, 8000);
        }
    }
    
    // Stop displaying facts
    function stopFactsInterval() {
        if (currentFactInterval) {
            clearInterval(currentFactInterval);
            currentFactInterval = null;
        }
    }
    
    // Display a random travel fact
    function displayRandomFact() {
        if (factDisplay) {
            const fact = getRandomTravelFact();
            factDisplay.innerHTML = `
                <div class="fact-title">Did you know?</div>
                <div>${fact}</div>
            `;
        }
    }
    
    // Check if destination exists or create a new one
    async function getOrCreateDestination(city, country) {
        // Check if destination already exists
        const response = await fetch(`/api/destinations/?name=${encodeURIComponent(city)}&country=${encodeURIComponent(country)}`);
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            return data.results[0].id;
        } else {
            // Create new destination
            const createResponse = await fetch('/api/destinations/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: city,
                    country: country,
                    description: `Travel information for ${city}, ${country}`
                })
            });
            
            const newDestination = await createResponse.json();
            return newDestination.id;
        }
    }
    
    // Generate travel advice for a destination
    async function generateAdvice(destinationId, hobbies = '') {
        let requestBody = {};
        
        // If hobbies are provided, include them in the request
        if (hobbies) {
            requestBody.hobbies = hobbies;
        }
        
        const response = await fetch(`/api/destinations/${destinationId}/generate_advice/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: Object.keys(requestBody).length ? JSON.stringify(requestBody) : undefined
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate travel advice');
        }
        
        return await response.json();
    }
    
    // Get travel advice for a destination
    async function getTravelAdvice(destinationId) {
        const response = await fetch(`/api/destinations/${destinationId}/`);
        return await response.json();
    }
    
    // Display results
    function displayResults(data, city, country) {
        if (!data || !data.advice || data.advice.length === 0) {
            showError('No travel advice found for this destination.');
            return;
        }
        
        let html = `
            <div class="results-header">
                <h2>${city}, ${country}</h2>
            </div>
        `;
        
        // Map category names to display names
        const categoryDisplayNames = {
            'safety': 'Safety Information',
            'weather': 'Weather and Climate',
            'culture': 'Cultural Guide',
            'transportation': 'Transportation',
            'attractions': 'Attractions and Activities'
        };
        
        // Sort advice by category order
        const categoryOrder = ['safety', 'weather', 'culture', 'transportation', 'attractions'];
        const sortedAdvice = [...data.advice].sort((a, b) => {
            return categoryOrder.indexOf(a.category) - categoryOrder.indexOf(b.category);
        });
        
        // Create sections for each advice category
        sortedAdvice.forEach(advice => {
            const displayName = categoryDisplayNames[advice.category] || advice.category;
            
            html += `
                <div class="section">
                    <div class="section-header">
                        <h3>${displayName}</h3>
                        <span class="arrow">&#9660;</span>
                    </div>
                    <div class="section-content">
                        ${formatContent(advice.content)}
                    </div>
                </div>
            `;
        });
        
        // Add follow-up question section
        html += `
            <div class="follow-up-section">
                <h4 class="follow-up-title">Have a follow-up question?</h4>
                <form class="follow-up-form" data-destination-id="${data.id}">
                    <div class="follow-up-input">
                        <input type="text" class="follow-up-input-field" placeholder="Ask about specific interests, activities, or recommendations...">
                        <button type="submit">Ask</button>
                    </div>
                </form>
            </div>
        `;
        
        resultsContainer.innerHTML = html;
        resultsContainer.style.display = 'block';
        
        // Initialize collapsible sections and follow-up handlers
        initializeCollapsibleSections();
    }
    
    // Format content by converting paragraphs
    function formatContent(content) {
        if (!content) return '';
        
        // Split by double newlines and create paragraphs
        return content.split('\n\n')
            .map(para => `<p>${para.replace(/\n/g, '<br>')}</p>`)
            .join('');
    }
    
    // Show loading indicator
    function showLoading() {
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
        hideError();
    }
    
    // Hide loading indicator
    function hideLoading() {
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    // Show error message
    function showError(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }
    
    // Hide error message
    function hideError() {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }
}); 