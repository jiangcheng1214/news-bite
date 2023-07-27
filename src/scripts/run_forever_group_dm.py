
# load ig account from file

import datetime
import os

from instagram.InstagramAPIManager import InstagramAPIManager, InstagramAPIManagerAccountType
from utils.Logging import info, error
import time

trigger_hours = [0, 6, 12, 18]
users_to_invite_per_group = 24
dm_pool_size_multiplier = 2
my_user_id = '545357425'
crypto_user_id = '60768462406'
fintech_user_id = '60649820282'
crypto_poster_photo_path = os.path.join(os.path.dirname(
    __file__), '..', '..', 'data', 'crypto_poster.jpg')
fintech_poster_photo_path = os.path.join(os.path.dirname(
    __file__), '..', '..', 'data', 'fintech_poster.jpg')

ig_accounts_file_path = os.path.join(
    os.path.dirname(__file__), '..', '..', 'credentials', 'ig_acc.txt')
ig_accounts = []
with open(ig_accounts_file_path, 'r') as f:
    for line in f.readlines():
        line = line.strip()
        if len(line) > 0:
            parts = line.split('----')
            ig_accounts.append([parts[0], parts[1]])
dm_pool_size_target = users_to_invite_per_group * \
    len(ig_accounts) * dm_pool_size_multiplier


def get_dm_user_pool(apiManager: InstagramAPIManager, existing_users=set(), visited_influencer_ids=set(), retry=False):
    past_dm_user_ids = set(apiManager.get_past_dm_user_ids())
    all_users_to_dm = existing_users
    visited_influencer_ids = visited_influencer_ids
    try:
        seed_influencers = apiManager.get_non_private_influencers(
            seed_query='crypto')
    except Exception as e:
        if not retry:
            error(
                f"Exception in getting seed influencers for account {apiManager.username}: {e}. Retrying...")
            time.sleep(5)
            return get_dm_user_pool(apiManager, all_users_to_dm, visited_influencer_ids, retry=True)
        else:
            error(
                f"Exception in getting seed influencers for account {apiManager.username}: {e}")
            return all_users_to_dm, visited_influencer_ids
    try:
        for influencer in seed_influencers:
            if influencer.pk in visited_influencer_ids:
                continue
            followers = apiManager.get_follower_ids(influencer.username)
            if len(followers) == 0:
                error(
                    f"0 followers for influencer {influencer.username}")
                return all_users_to_dm, visited_influencer_ids
            visited_influencer_ids.add(influencer.pk)
            for follower_user_id in followers:
                if follower_user_id not in past_dm_user_ids and follower_user_id not in all_users_to_dm:
                    all_users_to_dm.add(follower_user_id)
                    time.sleep(0.1)
                if len(all_users_to_dm) >= dm_pool_size_target:
                    break
            info(
                f"users pool to DM: {len(all_users_to_dm)}, target: {dm_pool_size_target} influencer: {influencer.username}")
            time.sleep(2)
            if len(all_users_to_dm) >= dm_pool_size_target:
                break
    except Exception as e:
        error(
            f"Exception in getting followers for seed influencers for account {apiManager.username}: {e}")
        error(
            f"Early return with {len(all_users_to_dm)} users to DM")
        return all_users_to_dm, visited_influencer_ids
    info(f"users pool to DM: {len(all_users_to_dm)}")
    return all_users_to_dm, visited_influencer_ids


def group_dm():
    i = 0
    total_user_dm_reached = 0
    total_user_failed_to_add = 0
    all_users_to_dm = set()
    visited_influencer_ids = set()
    for account in ig_accounts:
        un, pw = account
        try:
            apiManager = InstagramAPIManager(
                accountType=InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther, username=un, password=pw)
        except Exception as e:
            error(
                f"Exception in creating InstagramAPIManager for account {un}: {e}")
            continue
        if len(all_users_to_dm) < dm_pool_size_target:
            try:
                all_users_to_dm, visited_influencer_ids = get_dm_user_pool(
                    apiManager, all_users_to_dm, visited_influencer_ids)
            except Exception as e:
                error(
                    f"Exception in getting dm user pool for account {un}: {e}")
                continue
        else:
            all_users_to_dm_list = list(all_users_to_dm)
            break
    info(f"users pool to DM: {len(all_users_to_dm)}")
    for account in ig_accounts:
        un, pw = account
        try:
            apiManager = InstagramAPIManager(
                accountType=InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther, username=un, password=pw)
        except Exception as e:
            error(
                f"Exception in creating InstagramAPIManager for account {un}: {e}")
            continue
        thread_id = None
        attempt = 0
        while thread_id is None:
            attempt += 1
            try:
                next_user_id = all_users_to_dm_list.pop()
                msg = apiManager.client.direct_send(
                    '.', [my_user_id, next_user_id])
                thread_id = msg.thread_id
            except Exception as e:
                error(
                    f"Exception in creating thread for account {un} user_id: {next_user_id}: {e}")
                if attempt > 3:
                    break
        if thread_id is None:
            error(
                f"Failed to create thread for account {un} user_id: {next_user_id}")
            continue
        users_in_this_group = [my_user_id, next_user_id]
        failed_to_add_user_count = 0
        consequtive_failure = 0
        while len(all_users_to_dm_list) > 0 and len(users_in_this_group) < users_to_invite_per_group and consequtive_failure < 5:
            try:
                next_user_id = all_users_to_dm_list.pop()
                success = apiManager.client.add_users_to_direct_thread(
                    thread_id=thread_id, user_ids=[next_user_id])
                if success:
                    users_in_this_group.append(next_user_id)
                    consequtive_failure = 0
                else:
                    failed_to_add_user_count += 1
                    consequtive_failure += 1
            except Exception as e:
                error(
                    f"Exception in adding user to group for account {un} user_id: {next_user_id}: {e}")
                failed_to_add_user_count += 1
                consequtive_failure += 1
                continue
        if len(users_in_this_group) < 5:
            error(
                f"Failed to add enough users to group for account {un}")
            continue
        info(
            f"DMing from {un} to {len(users_in_this_group)} users, index: {i}")
        try:
            photo_share = apiManager.client.direct_send_photo(
                path=crypto_poster_photo_path, thread_ids=[thread_id])
            info(f"DM photo share result: {photo_share}")
        except Exception as e:
            error(
                f"Exception in DMing photo share: {e}\nusername: {un}. dm user ids: {users_in_this_group}")
        try:
            msg = apiManager.client.direct_send(
                '🔥 Hot crypto currency news updates 🔥\n @crypto_news_pulse <<< Follow and catch opportunities!', thread_ids=[thread_id])
            info(f"DM result: {msg}")
            apiManager.record_dm_user_ids(users_in_this_group)
            info(
                f"DMed from {un} to {len(users_in_this_group)} users, index: {i}, failed to add user count: {failed_to_add_user_count}")
            total_user_dm_reached += len(users_in_this_group)
        except Exception as e:
            error(
                f"Exception in DMing: {e}\nusername: {un}. dm user ids: {users_in_this_group}")
        try:
            profile_share = apiManager.client.direct_profile_share(
                user_id=crypto_user_id, thread_ids=[thread_id])
            info(f"DM profile share result: {profile_share}")
        except Exception as e:
            error(
                f"Exception in DMing profile share: {e}\nusername: {un}. dm user ids: {users_in_this_group}")
        total_user_failed_to_add += failed_to_add_user_count
        time.sleep(5)
        i += 1
    info(
        f"Total user DM reached: {total_user_dm_reached}, failed to add: {total_user_failed_to_add}")


if __name__ == "__main__":
    while True:
        try:
            current_start_time = datetime.datetime.now()
            hour = current_start_time.hour
            next_hour_start_time = (current_start_time + datetime.timedelta(hours=1)
                                    ).replace(minute=0, second=0, microsecond=0)
            if hour % 2 == 0:
                group_dm()
            sec_until_next_start = (
                next_hour_start_time - datetime.datetime.now()).seconds
            info(f"Seconds until the next hour starts: {sec_until_next_start}")
            time.sleep(sec_until_next_start+5)
        except Exception as e:
            error(f"Exception in sending dm: {e}")
            time.sleep(300)
