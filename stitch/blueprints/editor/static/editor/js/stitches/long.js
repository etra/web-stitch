/**
 * Long Stitches (Vertical and Horizontal)
 */

import { BaseStitch } from './base.js';

export class LongVerticalStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'long-vertical';
        this.name = 'Long Stitch (Vertical)';
        this.category = 'Long Stitch';
        this.description = 'Texture & accents';
        this.icon = '|';
    }

    draw(ctx, x, y, size, color) {
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + size / 2, y + padding);
        ctx.lineTo(x + size / 2, y + size - padding);
        ctx.stroke();
    }
}

export class LongHorizontalStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'long-horizontal';
        this.name = 'Long Stitch (Horizontal)';
        this.category = 'Long Stitch';
        this.description = 'Texture & accents';
        this.icon = '―';
    }

    draw(ctx, x, y, size, color) {
        const padding = size * 0.1;

        ctx.beginPath();
        ctx.moveTo(x + padding, y + size / 2);
        ctx.lineTo(x + size - padding, y + size / 2);
        ctx.stroke();
    }
}
