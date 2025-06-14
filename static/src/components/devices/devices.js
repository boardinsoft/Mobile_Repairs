/** @odoo-module **/

import { Component, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Componente para mostrar estadísticas del cliente en tiempo real
 */
export class CustomerRepairStats extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            isLoading: true,
            stats: {
                total_repairs: 0,
                completed_repairs: 0,
                pending_repairs: 0
            }
        });
        
        onMounted(() => this.loadStats());
    }
    
    async loadStats() {
        try {
            // Obtener el ID del cliente actual desde el contexto
            const customerId = this.env.model.root.resId;
            
            if (!customerId) {
                this.state.isLoading = false;
                return;
            }
            
            // Cargar estadísticas desde el servidor
            const stats = await this.rpc(`/repair/customer/${customerId}/stats`);
            
            this.state.stats = stats;
            this.state.isLoading = false;
            
            // Actualizar elementos en el DOM si existen
            this.updateStatsInDOM(stats);
            
        } catch (error) {
            console.error("Error loading customer stats:", error);
            this.state.isLoading = false;
        }
    }
    
    updateStatsInDOM(stats) {
        // Actualizar contadores en los elementos específicos
        const totalElement = document.getElementById('total_repairs');
        const completedElement = document.getElementById('completed_repairs');
        const pendingElement = document.getElementById('pending_repairs');
        
        if (totalElement) totalElement.textContent = stats.total_repairs;
        if (completedElement) completedElement.textContent = stats.completed_repairs;
        if (pendingElement) pendingElement.textContent = stats.pending_repairs;
        
        // Cargar reparaciones recientes
        this.loadRecentRepairs();
    }
    
    async loadRecentRepairs() {
        try {
            const customerId = this.env.model.root.resId;
            
            if (!customerId) return;
            
            const result = await this.rpc(`/repair/customer/${customerId}/recent_repairs`);
            
            const container = document.getElementById('recent_repairs_container');
            if (container && result.html) {
                container.innerHTML = result.html;
            }
            
        } catch (error) {
            console.error("Error loading recent repairs:", error);
            
            const container = document.getElementById('recent_repairs_container');
            if (container) {
                container.innerHTML = `
                    <div class="alert alert-warning" role="alert">
                        <strong>Error:</strong> No se pudieron cargar las reparaciones recientes.
                    </div>
                `;
            }
        }
    }
    
    async refreshData() {
        this.state.isLoading = true;
        await this.loadStats();
    }
}

CustomerRepairStats.template = "mobile_repair_orders.CustomerRepairStats";

// Auto-ejecutar cuando se carga la página del cliente
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si estamos en la vista de formulario de cliente
    if (window.location.href.includes('res.partner') && 
        window.location.href.includes('view_type=form')) {
        
        // Esperar un poco para que Odoo termine de cargar
        setTimeout(() => {
            const customerId = extractCustomerIdFromURL();
            if (customerId) {
                loadCustomerStats(customerId);
            }
        }, 1000);
    }
});

function extractCustomerIdFromURL() {
    const match = window.location.href.match(/id=(\d+)/);
    return match ? parseInt(match[1]) : null;
}

async function loadCustomerStats(customerId) {
    try {
        // Realizar llamada AJAX a nuestro controlador
        const response = await fetch(`/repair/customer/${customerId}/stats`, {
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
        
        const data = await response.json();
        
        if (data.result) {
            const container = document.getElementById('recent_repairs_container');
            if (container) {
                container.innerHTML = data.result.html;
            }
        }
        
    } catch (error) {
        console.error('Error loading recent repairs:', error);
        
        const container = document.getElementById('recent_repairs_container');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <strong>Error:</strong> No se pudieron cargar las reparaciones recientes.
                </div>
            `;
        }
    }
}

// Registrar el componente
registry.category("fields").add("customer_repair_stats", CustomerRepairStats);