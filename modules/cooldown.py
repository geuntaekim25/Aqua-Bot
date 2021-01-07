from discord.ext import commands
from modules.util import get_rank


class CustomCooldown:
    def __init__(self):
        self.default_mapping = commands.CooldownMapping.from_cooldown(1, 40, commands.BucketType.user)
        self.voters_mapping = commands.CooldownMapping.from_cooldown(1, 20, commands.BucketType.user)
        self.patrons_mapping = commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)
        self.mod_mapping = commands.CooldownMapping.from_cooldown(1, 0, commands.BucketType.user)

    def __call__(self, ctx: commands.Context):
        if self.voters_mapping._bucket_key(ctx.message) in get_rank('voter'):
            bucket = self.voters_mapping.get_bucket(ctx.message)
        elif self.patrons_mapping._bucket_key(ctx.message) in get_rank('patron'):
            bucket = self.patrons_mapping.get_bucket(ctx.message)
        elif self.mod_mapping._bucket_key(ctx.message) in get_rank('mod'):
            bucket = self.mod_mapping.get_bucket(ctx.message)
        else:
            bucket = self.default_mapping.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True