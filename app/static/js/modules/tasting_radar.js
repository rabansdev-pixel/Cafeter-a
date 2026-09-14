/**
 * Módulo: TastingRadar
 * Renderiza y actualiza dinámicamente un gráfico de radar sensorial en SVG interactivo.
 */
export function initTastingRadar() {
    const radarSvg = document.getElementById('sensory-radar-svg');
    const tabs = document.querySelectorAll('.radar-tab-btn');
    const notesContainer = document.getElementById('radar-notes-list');
    const roastLabel = document.getElementById('radar-roast-val');
    const altitudeLabel = document.getElementById('radar-altitude-val');
    const processLabel = document.getElementById('radar-process-val');

    if (!radarSvg) return;

    const centerX = 190;
    const centerY = 190;
    const maxRadius = 130;
    const axes = [
        { key: 'acidity', label: 'Acidez', angle: -90 },
        { key: 'sweetness', label: 'Dulzura', angle: -18 },
        { key: 'aroma', label: 'Aroma', angle: 54 },
        { key: 'body', label: 'Cuerpo', angle: 126 },
        { key: 'roast', label: 'Tueste', angle: 198 }
    ];

    function calculatePoint(angleDeg, value) {
        const rad = (angleDeg * Math.PI) / 180;
        const r = (value / 10) * maxRadius;
        return {
            x: centerX + r * Math.cos(rad),
            y: centerY + r * Math.sin(rad)
        };
    }

    function renderRadar(metrics) {
        // Convert roast string to 1-10 numeric scale
        let roastNum = 5;
        if (metrics.roast_level.toLowerCase().includes('claro')) roastNum = 3;
        if (metrics.roast_level.toLowerCase().includes('medio')) roastNum = 6;
        if (metrics.roast_level.toLowerCase().includes('oscuro')) roastNum = 9;

        const values = {
            acidity: metrics.acidity || 7,
            sweetness: metrics.sweetness || 8,
            aroma: metrics.aroma || 9,
            body: metrics.body || 6,
            roast: roastNum
        };

        const points = axes.map(axis => {
            const pt = calculatePoint(axis.angle, values[axis.key]);
            return `${pt.x},${pt.y}`;
        }).join(' ');

        // Update polygon points
        const polygon = document.getElementById('radar-polygon');
        if (polygon) {
            polygon.setAttribute('points', points);
        }

        // Update dots
        axes.forEach(axis => {
            const dot = document.getElementById(`radar-dot-${axis.key}`);
            if (dot) {
                const pt = calculatePoint(axis.angle, values[axis.key]);
                dot.setAttribute('cx', pt.x);
                dot.setAttribute('cy', pt.y);
            }
        });

        // Update flavor notes pills safely without innerHTML (Elimina DOM-based XSS en Snyk)
        if (notesContainer && Array.isArray(metrics.notes)) {
            const pillNodes = metrics.notes.map(note => {
                const span = document.createElement('span');
                span.className = 'tag-note';
                span.style.borderColor = 'var(--color-accent-gold)';
                span.style.color = 'var(--color-text-primary)';
                span.style.fontSize = '0.85rem';
                span.style.padding = '0.35rem 0.85rem';
                span.textContent = String(note);
                return span;
            });
            notesContainer.replaceChildren(...pillNodes);
        }

        if (roastLabel) roastLabel.textContent = metrics.roast_level || 'Medio';
    }

    // Attach listeners to tabs
    tabs.forEach(tab => {
        tab.addEventListener('click', async () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const productId = tab.dataset.productId;
            const altitude = tab.dataset.altitude;
            const process = tab.dataset.process;

            if (altitudeLabel) altitudeLabel.textContent = altitude || '1.950 msnm';
            if (processLabel) processLabel.textContent = process || 'Lavado';

            try {
                const res = await fetch(`/api/products/${productId}/radar`);
                const data = await res.json();
                if (data.status === 'success') {
                    renderRadar(data.data.radar);
                }
            } catch (err) {
                console.error('Error fetching radar data:', err);
            }
        });
    });

    // Render initial radar with first tab's data
    const activeTab = document.querySelector('.radar-tab-btn.active') || tabs[0];
    if (activeTab) {
        activeTab.click();
    }
}
