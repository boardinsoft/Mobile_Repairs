/** @odoo-module **/

import { Component, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

/**
 * Componente de gráfico de estados para el dashboard de reparaciones
 */
export class RepairStatesChart extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            isLoading: true,
            chartData: null
        });
        
        onMounted(() => this.loadChart());
    }
    
    async loadChart() {
        try {
            // Cargar librería Chart.js
            await loadJS("/web/static/lib/Chart/Chart.js");
            
            // Obtener datos del servidor
            const data = await this.rpc("/repair/dashboard/chart_data");
            
            this.state.chartData = data.states_chart;
            this.state.isLoading = false;
            
            // Renderizar gráfico
            this.renderChart();
            
        } catch (error) {
            console.error("Error loading chart:", error);
            this.state.isLoading = false;
        }
    }
    
    renderChart() {
        if (!this.state.chartData || !window.Chart) return;
        
        const canvas = this.el.querySelector('canvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: this.state.chartData.labels,
                datasets: [{
                    data: this.state.chartData.data,
                    backgroundColor: this.state.chartData.backgroundColor,
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
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
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
    }
}

RepairStatesChart.template = "mobile_repair_orders.RepairStatesChart";

/**
 * Componente de gráfico de actividad diaria
 */
export class DailyActivityChart extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            isLoading: true,
            chartData: null
        });
        
        onMounted(() => this.loadChart());
    }
    
    async loadChart() {
        try {
            await loadJS("/web/static/lib/Chart/Chart.js");
            
            const data = await this.rpc("/repair/dashboard/chart_data");
            
            this.state.chartData = data.daily_activity;
            this.state.isLoading = false;
            
            this.renderChart();
            
        } catch (error) {
            console.error("Error loading chart:", error);
            this.state.isLoading = false;
        }
    }
    
    renderChart() {
        if (!this.state.chartData || !window.Chart) return;
        
        const canvas = this.el.querySelector('canvas');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.state.chartData.labels,
                datasets: [{
                    label: 'Órdenes Recibidas',
                    data: this.state.chartData.data,
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderColor: this.state.chartData.borderColor,
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
                    legend: {
                        display: false
                    },
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
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            stepSize: 1,
                            font: {
                                size: 11
                            }
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
    }
}

DailyActivityChart.template = "mobile_repair_orders.DailyActivityChart";

// Registrar componentes en el registry de Odoo
registry.category("fields").add("repair_states_chart", RepairStatesChart);
registry.category("fields").add("daily_activity_chart", DailyActivityChart);