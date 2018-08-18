import binascii
import os
import aiohttp
from functools import wraps

from sanic.log import logger
from sanic import exceptions

from pubgate import __version__
from pubgate.api.v1.db.models import User


async def deliver_task(recipient, activity):
    logger.info(f" Delivering {make_label(activity)} ===> {recipient}")
    async with aiohttp.ClientSession() as session:

        async with session.get(recipient,
                               headers={'Accept': 'application/activity+json'}
                               ) as resp:
            logger.info(resp)
            profile = await resp.json()

        async with session.post(profile["inbox"],
                                json=activity,
                                headers={
                                    'Accept': 'application/activity+json',
                                    "Content-Type": 'application/activity+json',
                                    "User-Agent": f"Pubgate v:{__version__}",
                                }
                                ) as resp:
            logger.info(resp)


async def deliver(activity, recipients):
    # TODO deliver
    # TODO retry over day if fails

    for recipient in recipients:
        try:
            await deliver_task(recipient, activity)
        except Exception as e:
            logger.error(e)


def make_label(activity):
    label = activity["type"]
    if isinstance(activity["object"], dict):
        label = f'{label}: {activity["object"]["type"]}'
    return label


def random_object_id() -> str:
    """Generates a random object ID."""
    return binascii.hexlify(os.urandom(8)).decode("utf-8")


def auth_required(handler=None):
    @wraps(handler)
    async def wrapper(request, *args, **kwargs):
        user = await User.find_one(dict(username=kwargs["user_id"],
                                        token=request.token))
        if not user:
            raise exceptions.Unauthorized("Auth required.")

        return await handler(request, *args, **kwargs)
    return wrapper
