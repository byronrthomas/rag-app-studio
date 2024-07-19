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

// @ts-expect-error error-arg-is-any
export function jsonRequest(url: string, data: Record<string, unknown>, onError: (e) => void = (_) => { }): Promise<unknown> {
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
        .catch(error => { onError(error); alert(`Error: ${error}. Please adjust your request and try again.`) });
}

// @ts-expect-error error-arg-is-any
export function jsonRequestThenReload(url: string, data: Record<string, unknown>, onError: (e) => void = (_) => { }): Promise<void> {
    return jsonRequest(url, data, onError).then(() => {
        window.location.reload();
    });
}

