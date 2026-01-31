/**
 * Backstitches (all 4 directions)
 */

import { BaseStitch } from './base.js';

export class BackstitchHorizontal extends BaseStitch {
    constructor() {
        super();
        this.id = 'backstitch-horizontal';
        this.name = 'Backstitch (Horizontal)';
        this.category = 'Backstitch';
        this.description = 'Outlines & definition';
        this.icon = '─';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;

        ctx.beginPath();
        ctx.moveTo(x, y + mid);
        ctx.lineTo(x + size, y + mid);
        ctx.stroke();
    }
}

export class BackstitchVertical extends BaseStitch {
    constructor() {
        super();
        this.id = 'backstitch-vertical';
        this.name = 'Backstitch (Vertical)';
        this.category = 'Backstitch';
        this.description = 'Outlines & definition';
        this.icon = '│';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;

        ctx.beginPath();
        ctx.moveTo(x + mid, y);
        ctx.lineTo(x + mid, y + size);
        ctx.stroke();
    }
}

export class BackstitchSlash extends BaseStitch {
    constructor() {
        super();
        this.id = 'backstitch-slash';
        this.name = 'Backstitch (/)';
        this.category = 'Backstitch';
        this.description = 'Outlines & definition';
        this.icon = '╱';
    }

    draw(ctx, x, y, size, color) {
        ctx.beginPath();
        ctx.moveTo(x, y + size);
        ctx.lineTo(x + size, y);
        ctx.stroke();
    }
}

export class BackstitchBackslash extends BaseStitch {
    constructor() {
        super();
        this.id = 'backstitch-backslash';
        this.name = 'Backstitch (\\)';
        this.category = 'Backstitch';
        this.description = 'Outlines & definition';
        this.icon = '╲';
    }

    draw(ctx, x, y, size, color) {
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + size, y + size);
        ctx.stroke();
    }
}
