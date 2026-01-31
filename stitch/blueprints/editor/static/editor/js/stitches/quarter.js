/**
 * Quarter Stitches (all 4 corners)
 */

import { BaseStitch } from './base.js';

export class QuarterTLStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'quarter-tl';
        this.name = 'Quarter (Top-Left)';
        this.category = 'Quarter';
        this.description = 'Fine detail';
        this.icon = '◸';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + padding, y + padding);
        ctx.lineTo(x + mid, y + mid);
        ctx.stroke();
    }
}

export class QuarterTRStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'quarter-tr';
        this.name = 'Quarter (Top-Right)';
        this.category = 'Quarter';
        this.description = 'Fine detail';
        this.icon = '◹';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + size - padding, y + padding);
        ctx.lineTo(x + mid, y + mid);
        ctx.stroke();
    }
}

export class QuarterBLStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'quarter-bl';
        this.name = 'Quarter (Bottom-Left)';
        this.category = 'Quarter';
        this.description = 'Fine detail';
        this.icon = '◺';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + padding, y + size - padding);
        ctx.lineTo(x + mid, y + mid);
        ctx.stroke();
    }
}

export class QuarterBRStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'quarter-br';
        this.name = 'Quarter (Bottom-Right)';
        this.category = 'Quarter';
        this.description = 'Fine detail';
        this.icon = '◿';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + size - padding, y + size - padding);
        ctx.lineTo(x + mid, y + mid);
        ctx.stroke();
    }
}
