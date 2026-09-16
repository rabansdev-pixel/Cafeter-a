import { initProductScene } from './modules/product_scene.js';
import { initHeroProduct } from './modules/hero_product.js';
import { initTastingRadar } from './modules/tasting_radar.js';
import { initCafe } from './modules/cafe.js';
import { initHomeAnimations } from './modules/home_animations.js';
import { initNavigation } from './modules/navigation.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log('☕ ZERO-DAY COFFEE iniciada');

    // Inicializar micro-interacciones y módulos
    initHeroProduct();
    initTastingRadar();
    initCafe();
    initNavigation();
    initHomeAnimations();
    initProductScene();
});
