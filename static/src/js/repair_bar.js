/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc";
import { Chart } from "web/static/lib/Chart/Chart";

export class RepairBar extends Component {
    async willStart() {
        this.chartData = await jsonrpc('/mobile_repair_orders/dashboard/bars', {});
    }

    mounted() {
        const ctx = this.el.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: this.chartData,
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}
RepairBar.template = 'mobile_repair_orders.RepairBar';

registry.category('fields').add('mobile_repair_orders_repair_bar', RepairBar); 