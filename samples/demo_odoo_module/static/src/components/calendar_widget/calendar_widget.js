/** @odoo-module */
import { Component, useState, onMounted } from '@odoo/owl';
import { registry } from '@web/core/registry';

export class CalendarWidget extends Component {
    static template = 'demo.CalendarWidget';
    static props = ['title'];
    setup() {
        this.state = useState({ count: 0 });
        onMounted(() => { this.state.count += 1; });
    }
    formatMonth(month) {
        return `Month ${month}`;
    }
}
registry.category('actions').add('demo.calendar_widget', CalendarWidget);
