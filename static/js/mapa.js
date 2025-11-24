// Funções auxiliares para o mapa
class MapaManager {
    constructor() {
        this.map = null;
        this.markers = [];
    }

    inicializarMapa(lat = -23.5505, lng = -46.6333, zoom = 10) {
        this.map = L.map('map').setView([lat, lng], zoom);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        return this.map;
    }

    adicionarMarcador(ong) {
        if (!ong.lat || !ong.lng) return null;

        const marker = L.marker([ong.lat, ong.lng]).addTo(this.map);

        const popupContent = this.criarPopup(ong);
        marker.bindPopup(popupContent);

        this.markers.push(marker);
        return marker;
    }

    criarPopup(ong) {
        const isUsuario = !window.currentUserIsONG;

        return `
            <div class="p-3 min-w-64">
                <h3 class="font-bold text-lg text-gray-800 mb-1">${ong.nome}</h3>
                <p class="text-gray-600 text-sm mb-2">
                    <i class="fas fa-map-marker-alt mr-1"></i>${ong.cidade}
                </p>
                <p class="text-gray-700 text-sm mb-3">${ong.descricao || 'Sem descrição disponível.'}</p>
                
                <div class="mb-3">
                    ${ong.causas.map(causa => 
                        `<span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1 mb-1">${causa}</span>`
                    ).join('')}
                </div>

                ${isUsuario ? 
                    `<a href="/voluntariar/${ong.id}" 
                        class="w-full bg-green-600 text-white text-center py-2 px-4 rounded hover:bg-green-700 transition block text-sm font-semibold">
                        <i class="fas fa-hand-holding-heart mr-1"></i>Quero Ajudar
                    </a>` : 
                    `<span class="text-gray-500 text-sm">Faça login como voluntário para se candidatar</span>`
                }
            </div>
        `;
    }

    ajustarVisualizacao() {
        if (this.markers.length === 0) return;

        const group = new L.featureGroup(this.markers);
        this.map.fitBounds(group.getBounds().pad(0.1));
    }

    limparMarcadores() {
        this.markers.forEach(marker => this.map.removeLayer(marker));
        this.markers = [];
    }
}

// Auto-complete para cidades
function inicializarAutocomplete() {
    const cidadeInput = document.getElementById('cidade');
    if (!cidadeInput) return;

    // Lista de cidades brasileiras (exemplo)
    const cidades = [
        'São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Porto Alegre',
        'Brasília', 'Salvador', 'Fortaleza', 'Recife', 'Curitiba', 'Goiânia'
    ];

    cidadeInput.addEventListener('input', function(e) {
        // Implementar lógica de auto-complete aqui
        // Pode integrar com API de CEP ou serviços similares
    });
}

// Inicialização quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar autocomplete
    inicializarAutocomplete();

    // Verificar se existe elemento do mapa na página
    if (document.getElementById('map')) {
        window.mapaManager = new MapaManager();
        window.mapaManager.inicializarMapa();

        // Carregar ONGs no mapa
        fetch('/api/ongs')
            .then(response => response.json())
            .then(ongs => {
                ongs.forEach(ong => {
                    window.mapaManager.adicionarMarcador(ong);
                });
                window.mapaManager.ajustarVisualizacao();
            })
            .catch(console.error);
    }
});