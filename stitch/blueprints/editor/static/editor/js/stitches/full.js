/**
 * Full Cross Stitch
 */

import { BaseStitch } from './base.js';

export class FullStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'full';
        this.name = 'Full Cross';
        this.category = 'Full & Half';
        this.description = 'Main stitch, full coverage';
        this.icon = '✕';
    }

    draw(ctx, x, y, size, color) {
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + padding, y + padding);
        ctx.lineTo(x + size - padding, y + size - padding);
        ctx.moveTo(x + size - padding, y + padding);
        ctx.lineTo(x + padding, y + size - padding);
        ctx.stroke();
    }
}
