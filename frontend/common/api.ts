// const HOST = 'http://localhost:8000';
const HOST = "https://ragstudiooqrt8jjsde-a27c45490b0ac66c.tec-s1.onthetaedgecloud.com";
export function buildUrl(path: string): string {
  return `${HOST}${path}`;
}
export function jsonRequest(url: string, data: Record<string, unknown>): Promise<unknown> {
  return fetch(buildUrl(url), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  }).then(response => response.json())
    .catch(error => console.error('Error:', error));
}export function jsonRequestThenReload(url: string, data: Record<string, unknown>): Promise<void> {
  return jsonRequest(url, data).then(() => {
    window.location.reload();
  });
}

