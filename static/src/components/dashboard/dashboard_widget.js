/** @odoo-module **/

import { loadJS } from "@web/core/assets";

/**
 * Inicialización de gráficos del dashboard cuando se carga la página
 */
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si estamos en el dashboard de reparaciones
    if (window.location.href.includes('repair.dashboard') || 
        document.querySelector('.o_repair_dashboard')) {
        
        // Esperar un poco para que Odoo termine de cargar
        setTimeout(() => {
            initializeDashboardCharts();
        }, 1000);
    }
});

async function initializeDashboardCharts() {
    try {
        // Cargar Chart.js
        await loadJS("/web/static/lib/Chart/Chart.js");
        
        // Inicializar gráficos
        await Promise.all([
            initializeStatesChart(),
            initializeDailyChart()
        ]);
        
    } catch (error) {
        console.error('Error initializing dashboard charts:', error);
    }
}

async function initializeStatesChart() {
    const canvas = document.getElementById('states_chart_canvas');
    if (!canvas || !window.Chart) return;
    
    try {
        // Obtener datos del servidor
        const response = await fetch('/repair/dashboard/chart_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {},
                id: Math.random()
            })
        });
        
        const result = await response.json();
        const chartData = result.result.states_chart;
        
        if (!chartData || !chartData.labels.length) {
            showNoDataMessage(canvas.parentElement, 'No hay datos de estados para mostrar');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.data,
                    backgroundColor: chartData.backgroundColor,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1000
                }
            }
        });
        
    } catch (error) {
        console.error('Error creating states chart:', error);
        showErrorMessage(canvas.parentElement, 'Error al cargar gráfico de estados');
    }
}

async function initializeDailyChart() {
    const canvas = document.getElementById('daily_chart_canvas');
    if (!canvas || !window.Chart) return;
    
    try {
        // Obtener datos del servidor
        const response = await fetch('/repair/dashboard/chart_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {},
                id: Math.random()
            })
        });
        
        const result = await response.json();
        const chartData = result.result.daily_activity;
        
        if (!chartData || !chartData.labels.length) {
            showNoDataMessage(canvas.parentElement, 'No hay datos de actividad para mostrar');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Órdenes Recibidas',
                    data: chartData.data,
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderColor: chartData.borderColor || '#28a745',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#28a745',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#28a745',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0, 0, 0, 0.1)' },
                        ticks: {
                            stepSize: 1,
                            font: { size: 11 }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 1500,
                    easing: 'easeInOutQuart'
                }
            }
        });
        
    } catch (error) {
        console.error('Error creating daily chart:', error);
        showErrorMessage(canvas.parentElement, 'Error al cargar gráfico de actividad');
    }
}

function showNoDataMessage(container, message) {
    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="text-center text-muted">
                <i class="fa fa-chart-pie fa-3x mb-3 opacity-25"></i>
                <p class="mb-0">${message}</p>
                <small>Los datos aparecerán cuando estén disponibles</small>
            </div>
        </div>
    `;
}

function showErrorMessage(container, message) {
    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="text-center text-warning">
                <i class="fa fa-exclamation-triangle fa-3x mb-3"></i>
                <p class="mb-0">${message}</p>
                <small>Intenta actualizar la página</small>
            </div>
        </div>
    `;
}

// Función global para actualizar gráficos
window.refreshDashboardCharts = function() {
    setTimeout(() => {
        initializeDashboardCharts();
    }, 500);
};