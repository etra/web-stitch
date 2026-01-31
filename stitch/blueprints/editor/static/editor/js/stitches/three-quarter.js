/**
 * Three-Quarter Stitches (all 4 variants)
 */

import { BaseStitch } from './base.js';

export class ThreeQuarterTLStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'three-quarter-tl';
        this.name = 'Three-Quarter (Top-Left)';
        this.category = 'Three-Quarter';
        this.description = 'Curves & smooth edges';
        this.icon = '⟋';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const padding = size * 0.1;

        ctx.beginPath();
        // Half stitch /
        ctx.moveTo(x + padding, y + size - padding);
        ctx.lineTo(x + size - padding, y + padding);
        // Quarter from TL
        ctx.moveTo(x + padding, y + padding);
        ctx.lineTo(x + mid, y + mid);
        ctx.stroke();
    }
}

export class ThreeQuarterTRStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'three-quarter-tr';
        this.name = 'Three-Quarter (Top-Right)';
        this.category = 'Three-Quarter';
        this.description = 'Curves & smooth edges';
        this.icon = '⟍';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const padding = size * 0.1;

        ctx.beginPath();
        // Half stitch \
        ctx.moveTo(x + padding, y + padding);
        ctx.lineTo(x + size - padding, y + size - padding);
        // Quarter from TR
        ctx.moveTo(x + size - padding, y + padding);
        ctx.lineTo(x + mid, y + mid);
        ctx.stroke();
    }
}

export class ThreeQuarterBLStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'three-quarter-bl';
        this.name = 'Three-Quarter (Bottom-Left)';
        this.category = 'Three-Quarter';
        this.description = 'Curves & smooth edges';
        this.icon = '⟍';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const padding = size * 0.1;

        ctx.beginPath();
        // Half stitch \
        ctx.moveTo(x + padding, y + padding);
        ctx.lineTo(x + size - padding, y + size - padding);
        // Quarter from BL
        ctx.moveTo(x + padding, y + size - padding);
        ctx.lineTo(x + mid, y + mid);
        ctx.stroke();
    }
}

export class ThreeQuarterBRStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'three-quarter-br';
        this.name = 'Three-Quarter (Bottom-Right)';
        this.category = 'Three-Quarter';
        this.description = 'Curves & smooth edges';
        this.icon = '⟋';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const padding = size * 0.1;

        ctx.beginPath();
        // Half stitch /
        ctx.moveTo(x + padding, y + size - padding);
        ctx.lineTo(x + size - padding, y + padding);
        // Quarter from BR
        ctx.moveTo(x + size - padding, y + size - padding);
        ctx.lineTo(x + mid, y + mid);
        ctx.stroke();
    }
}
