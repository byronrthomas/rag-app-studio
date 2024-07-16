const HOST = import.meta.env.VITE_API_PREFIX;
console.log('VITE_API_PREFIX:', HOST);
if (HOST === undefined) {
    throw new Error('VITE_API_PREFIX is not set');
}
if (HOST !== '' && HOST.endsWith('/')) {
    throw new Error('VITE_API_PREFIX should not end with /');
}
export function buildUrl(path: string): string {
    return `${HOST}${path}`;
}
export function jsonRequest(url: string, data: Record<string, unknown>): Promise<unknown> {
    if (!(url && url.startsWith('/'))) {
        throw new Error('URL cannot be empty and must start with /');
    }
    return fetch(buildUrl(url), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    }).then(response => response.json())
        .catch(error => console.error('Error:', error));
} export function jsonRequestThenReload(url: string, data: Record<string, unknown>): Promise<void> {
    return jsonRequest(url, data).then(() => {
        window.location.reload();
    });
}

