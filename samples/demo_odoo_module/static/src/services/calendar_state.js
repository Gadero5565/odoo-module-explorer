/** @odoo-module */
import { registry } from '@web/core/registry';

export const calendarStateService = {
    dependencies: ['orm', 'notification'],
    async start(env, { orm }) {
        const getDays = async (editionId) => orm.searchRead('demo.calendar.day', [['edition_id', '=', editionId]], ['name']);
        return { getDays };
    },
};
registry.category('services').add('calendar_state', calendarStateService);
