/**
 * Half Stitch (both directions)
 */

import { BaseStitch } from './base.js';

export class HalfSlashStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'half-slash';
        this.name = 'Half Stitch /';
        this.category = 'Full & Half';
        this.description = 'Faster fill, shading';
        this.icon = '/';
    }

    draw(ctx, x, y, size, color) {
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + padding, y + size - padding);
        ctx.lineTo(x + size - padding, y + padding);
        ctx.stroke();
    }
}

export class HalfBackslashStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'half-backslash';
        this.name = 'Half Stitch \\';
        this.category = 'Full & Half';
        this.description = 'Faster fill, shading';
        this.icon = '\\';
    }

    draw(ctx, x, y, size, color) {
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + padding, y + padding);
        ctx.lineTo(x + size - padding, y + size - padding);
        ctx.stroke();
    }
}
