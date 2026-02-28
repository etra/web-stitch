"""Service for communicating with the diffusion pixel-art microservice."""

import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)


class DiffusionServiceError(Exception):
    """Raised when the diffusion service is unavailable or returns an error."""


class DiffusionService:
    """Static methods for the diffusion pixel-art microservice."""

    @staticmethod
    def _base_url() -> str:
        return current_app.config.get('DIFFUSION_SERVICE_URL', 'https://service-gpu.ourstitch.com')

    @staticmethod
    def _auth_headers():
        return {'Authorization': 'Bearer etra:etra'}

    @staticmethod
    def get_health() -> dict:
        """Get health info from the diffusion service.

        Returns:
            Dict with 'status' ('ready'|'loading'|'offline') and 'busy' bool.
        """
        try:
            resp = requests.get(
                f'{DiffusionService._base_url()}/health',
                headers=DiffusionService._auth_headers(),
                timeout=5,
            )
            if resp.ok:
                return resp.json()
            return {'status': 'offline'}
        except Exception:
            return {'status': 'offline'}

    @staticmethod
    def get_status() -> str:
        return DiffusionService.get_health().get('status', 'offline')

    @staticmethod
    def is_available() -> bool:
        return DiffusionService.get_status() == 'ready'

    @staticmethod
    def submit_job(image_path, target_width: int, target_height: int, prompt: str = 'pixel art') -> str:
        """Submit a generation job to the diffusion service.

        Args:
            image_path: Path to the source image file.
            target_width: Desired pixel-art width.
            target_height: Desired pixel-art height.
            prompt: Style prompt for the diffusion model.

        Returns:
            Job ID string.

        Raises:
            DiffusionServiceError: On connection or HTTP errors.
        """
        url = DiffusionService._base_url()
        diffusion_prompt = f'Low resolution, 256 colors, no text, no watermarks, high contrast, no gradients, {prompt}'
        try:
            with open(str(image_path), 'rb') as f:
                resp = requests.post(
                    f'{url}/pixelate',
                    files={'image': ('image.png', f, 'image/png')},
                    data={'width': target_width, 'height': target_height, 'prompt': prompt},
                    headers=DiffusionService._auth_headers(),
                    timeout=30,
                )
        except requests.ConnectionError:
            raise DiffusionServiceError(
                'Cannot connect to diffusion service. Is the Docker container running?'
            )
        except requests.Timeout:
            raise DiffusionServiceError(
                'Diffusion service did not respond.'
            )

        if resp.status_code == 429:
            raise DiffusionServiceError(
                'Service is busy generating another image. Please wait and try again.'
            )

        if resp.status_code != 200:
            error_msg = 'Diffusion service error'
            try:
                error_msg = resp.json().get('error', error_msg)
            except Exception:
                pass
            raise DiffusionServiceError(error_msg)

        data = resp.json()
        return data['job_id']

    @staticmethod
    def get_job(job_id: str) -> dict:
        """Poll a generation job for status/progress/result.

        Args:
            job_id: Job ID from submit_job.

        Returns:
            Dict with status, step, total, elapsed, and optionally result or error.

        Raises:
            DiffusionServiceError: On connection errors.
        """
        url = DiffusionService._base_url()

        try:
            resp = requests.get(
                f'{url}/job/{job_id}',
                headers=DiffusionService._auth_headers(),
                timeout=5,
            )
        except Exception:
            raise DiffusionServiceError('Cannot connect to diffusion service.')

        if resp.status_code == 404:
            raise DiffusionServiceError('Job not found. It may have expired.')

        if not resp.ok:
            raise DiffusionServiceError('Failed to check job status.')

        return resp.json()
