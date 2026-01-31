/**
 * Stitches Module
 * Exports all stitch classes and provides utilities for registration
 */

// Base class
export { BaseStitch } from './base.js';

// Full & Half stitches
export { FullStitch } from './full.js';
export { HalfSlashStitch, HalfBackslashStitch } from './half.js';

// Quarter stitches
export {
    QuarterTLStitch,
    QuarterTRStitch,
    QuarterBLStitch,
    QuarterBRStitch
} from './quarter.js';

// Three-quarter stitches
export {
    ThreeQuarterTLStitch,
    ThreeQuarterTRStitch,
    ThreeQuarterBLStitch,
    ThreeQuarterBRStitch
} from './three-quarter.js';

// Special stitches
export { PetiteStitch, FrenchKnotStitch } from './special.js';

// Long stitches
export { LongVerticalStitch, LongHorizontalStitch } from './long.js';

// Backstitches
export {
    BackstitchHorizontal,
    BackstitchVertical,
    BackstitchSlash,
    BackstitchBackslash
} from './backstitch.js';

// Import all stitch classes
import { FullStitch } from './full.js';
import { HalfSlashStitch, HalfBackslashStitch } from './half.js';
import {
    QuarterTLStitch,
    QuarterTRStitch,
    QuarterBLStitch,
    QuarterBRStitch
} from './quarter.js';
import {
    ThreeQuarterTLStitch,
    ThreeQuarterTRStitch,
    ThreeQuarterBLStitch,
    ThreeQuarterBRStitch
} from './three-quarter.js';
import { PetiteStitch, FrenchKnotStitch } from './special.js';
import { LongVerticalStitch, LongHorizontalStitch } from './long.js';
import {
    BackstitchHorizontal,
    BackstitchVertical,
    BackstitchSlash,
    BackstitchBackslash
} from './backstitch.js';

/**
 * Array of all stitch classes
 * Use this to instantiate and register all default stitches
 */
export const allStitchClasses = [
    // Full & Half
    FullStitch,
    HalfSlashStitch,
    HalfBackslashStitch,

    // Quarter
    QuarterTLStitch,
    QuarterTRStitch,
    QuarterBLStitch,
    QuarterBRStitch,

    // Three-quarter
    ThreeQuarterTLStitch,
    ThreeQuarterTRStitch,
    ThreeQuarterBLStitch,
    ThreeQuarterBRStitch,

    // Special
    PetiteStitch,
    FrenchKnotStitch,

    // Long
    LongVerticalStitch,
    LongHorizontalStitch,

    // Backstitch
    BackstitchHorizontal,
    BackstitchVertical,
    BackstitchSlash,
    BackstitchBackslash
];

/**
 * Get all default stitch instances
 * @returns {BaseStitch[]} Array of stitch instances
 */
export function getAllStitches() {
    return allStitchClasses.map(StitchClass => new StitchClass());
}

/**
 * Register all default stitches with a renderer
 * @param {Renderer} renderer - The renderer instance
 */
export function registerAllStitches(renderer) {
    const stitches = getAllStitches();
    for (const stitch of stitches) {
        renderer.registerStitch(stitch);
    }
}
