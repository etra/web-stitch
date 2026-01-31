/**
 * Special Stitches (Petite, French Knot)
 */

import { BaseStitch } from './base.js';

export class PetiteStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'petite';
        this.name = 'Petite';
        this.category = 'Special';
        this.description = 'High-detail areas';
        this.icon = '✕';
    }

    draw(ctx, x, y, size, color) {
        const mid = size / 2;
        const quarter = size / 4;

        ctx.beginPath();
        // Small X in the center
        ctx.moveTo(x + mid - quarter, y + mid - quarter);
        ctx.lineTo(x + mid + quarter, y + mid + quarter);
        ctx.moveTo(x + mid + quarter, y + mid - quarter);
        ctx.lineTo(x + mid - quarter, y + mid + quarter);
        ctx.stroke();
    }
}

export class FrenchKnotStitch extends BaseStitch {
    constructor() {
        super();
        this.id = 'french-knot';
        this.name = 'French Knot';
        this.category = 'Special';
        this.description = 'Decorative dots';
        this.icon = '•';
    }

    draw(ctx, x, y, size, color) {
        const radius = size / 4;
        const centerX = x + size / 2;
        const centerY = y + size / 2;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.fill();
    }
}
