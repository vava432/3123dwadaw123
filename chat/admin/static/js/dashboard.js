class DatabaseViewer {
    constructor() {
        this.currentTable = null;
        this.init();
    }

    init() {
        this.loadStats();
        this.loadTables();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadStats();
            this.loadTables();
        });

        document.getElementById('execute-query').addEventListener('click', () => {
            this.executeQuery();
        });
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            if (stats.error) {
                this.showError(stats.error);
                return;
            }

            this.renderStats(stats);
        } catch (error) {
            this.showError('Ошибка загрузки статистики: ' + error.message);
        }
    }

    renderStats(stats) {
        const container = document.getElementById('stats-container');
        container.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${stats.users || 0}</div>
                <div class="stat-label">Пользователи</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.rooms || 0}</div>
                <div class="stat-label">Комнаты</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.messages || 0}</div>
                <div class="stat-label">Сообщения</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.files || 0}</div>
                <div class="stat-label">Файлы</div>
            </div>
        `;
    }

    async loadTables() {
        try {
            const response = await fetch('/api/tables');
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.renderTables(data.tables);
        } catch (error) {
            this.showError('Ошибка загрузки таблиц: ' + error.message);
        }
    }

    renderTables(tables) {
        const container = document.getElementById('tables-container');
        
        if (!tables || tables.length === 0) {
            container.innerHTML = '<div class="loading">Таблицы не найдены</div>';
            return;
        }

        container.innerHTML = tables.map(table => `
            <div class="table-card" onclick="dbViewer.loadTableData('${table}')">
                <h3>${table}</h3>
                <p>Нажмите для просмотра данных</p>
            </div>
        `).join('');
    }

    async loadTableData(tableName) {
        try {
            this.currentTable = tableName;
            
            // Обновляем активную таблицу
            document.querySelectorAll('.table-card').forEach(card => {
                card.classList.remove('active');
            });
            event.currentTarget.classList.add('active');

            const response = await fetch(`/api/table/${tableName}`);
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.renderTableData(data);
        } catch (error) {
            this.showError('Ошибка загрузки данных: ' + error.message);
        }
    }

    renderTableData(data) {
        const section = document.getElementById('table-view-section');
        const title = document.getElementById('table-view-title');
        const container = document.getElementById('table-data-container');

        section.style.display = 'block';
        title.textContent = `${data.table_name} (${data.count} записей)`;

        if (data.count === 0) {
            container.innerHTML = '<div class="loading">Таблица пуста</div>';
            return;
        }

        // Создаем таблицу
        let html = `
            <div class="table-responsive">
                <table class="data-table">
                    <thead>
                        <tr>
                            ${data.columns.map(col => `<th>${col.name}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.data.forEach(row => {
            html += '<tr>';
            data.columns.forEach(col => {
                let value = row[col.name];
                if (value === null || value === undefined) value = 'NULL';
                if (typeof value === 'string' && value.length > 100) {
                    value = value.substring(0, 100) + '...';
                }
                html += `<td title="${value}">${this.escapeHtml(value)}</td>`;
            });
            html += '</tr>';
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;
    }

    async executeQuery() {
        const query = document.getElementById('sql-query').value.trim();
        const resultContainer = document.getElementById('query-result');

        if (!query) {
            resultContainer.innerHTML = '<div class="notification error">Введите SQL запрос</div>';
            return;
        }

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            const result = await response.json();

            if (result.error) {
                resultContainer.innerHTML = `<div class="notification error">Ошибка: ${result.error}</div>`;
                return;
            }

            if (result.data) {
                let html = `<div class="notification success">Найдено записей: ${result.count}</div>`;
                
                if (result.data.length > 0) {
                    const columns = Object.keys(result.data[0]);
                    html += `
                        <div class="table-responsive">
                            <table class="data-table">
                                <thead>
                                    <tr>${columns.map(col => `<th>${col}</th>`).join('')}</tr>
                                </thead>
                                <tbody>
                                    ${result.data.map(row => `
                                        <tr>${columns.map(col => `<td>${this.escapeHtml(row[col])}</td>`).join('')}</tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    `;
                }
                
                resultContainer.innerHTML = html;
            } else {
                resultContainer.innerHTML = `<div class="notification success">${result.message}</div>`;
            }

        } catch (error) {
            resultContainer.innerHTML = `<div class="notification error">Ошибка: ${error.message}</div>`;
        }
    }

    escapeHtml(unsafe) {
        return unsafe
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    showError(message) {
        const container = document.createElement('div');
        container.className = 'notification error';
        container.textContent = message;
        document.querySelector('.container').prepend(container);
        
        setTimeout(() => container.remove(), 5000);
    }
}

// Инициализация при загрузке страницы
const dbViewer = new DatabaseViewer();