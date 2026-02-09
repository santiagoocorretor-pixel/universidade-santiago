const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3002;

const server = http.createServer((req, res) => {
    let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
    
    fs.readFile(filePath, (err, data) => {
        if (err) {
            res.writeHead(404, { 'Content-Type': 'text/html' });
            res.end('<h1>404 - Arquivo não encontrado</h1>');
            return;
        }
        
        const ext = path.extname(filePath).toLowerCase();
        let contentType = 'text/html';
        
        // Mapeamento de tipos MIME
        const mimeTypes = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.eot': 'application/vnd.ms-fontobject'
        };
        
        contentType = mimeTypes[ext] || 'application/octet-stream';
        
        // Adicionar headers de cache para arquivos estáticos
        const headers = { 'Content-Type': contentType };
        if (['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp', '.woff', '.woff2', '.ttf', '.eot'].includes(ext)) {
            headers['Cache-Control'] = 'public, max-age=31536000'; // 1 ano
        }
        
        res.writeHead(200, headers);
        res.end(data);
    });
});

server.listen(PORT, () => {
    console.log(`Servidor rodando em http://localhost:${PORT}/`);
});
