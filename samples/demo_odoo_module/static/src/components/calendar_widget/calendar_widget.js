/** Sample OWL component. JavaScript parsing will be added in Phase 5. */
import { Component } from "@odoo/owl";

export class CalendarWidget extends Component {
    static template = "demo.CalendarWidget";
    setup() {
        this.title = "Calendar";
    }
}
