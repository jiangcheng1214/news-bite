
# load ig account from file

import datetime
import os

from instagram.InstagramAPIManager import InstagramAPIManager, InstagramAPIManagerAccountType, get_past_dm_user_ids, get_past_visited_influencer_ids, get_todo_dm_user_ids, record_dm_user_ids, record_visited_influencer_id, set_todo_dm_user_ids
from utils.Logging import info, error
import time

users_to_invite_per_group = 24
dm_pool_size_multiplier = 1
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


def maintain_todo_dm_user_pool(target=dm_pool_size_target):
    available_ig_accounts = ig_accounts
    past_dm_user_ids = get_past_dm_user_ids(
        InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto)
    while True:
        visited_influencer_ids = get_past_visited_influencer_ids(
            InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto)
        todo_dm_user_ids = get_todo_dm_user_ids(
            InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto)
        if len(todo_dm_user_ids) >= target:
            break
        working_ig_account = available_ig_accounts.pop()
        un, pw = working_ig_account
        try:
            apiManager = InstagramAPIManager(
                accountType=InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther, username=un, password=pw)
        except Exception as e:
            error(
                f"Exception in creating InstagramAPIManager for account {un}: {e}")
            continue
        try:
            seed_influencers = apiManager.get_non_private_influencers(
                seed_query='crypto news')
        except Exception as e:
            error(
                f"Exception in getting seed influencers for account {apiManager.username}: {e}")
            continue
        try:
            for influencer in seed_influencers:
                todo_dm_user_ids_from_current_session = set()
                if influencer.pk in visited_influencer_ids:
                    continue
                candidate_user_ids = apiManager.get_follower_ids(
                    influencer.username)
                # candidate_user_ids = apiManager.get_commenter_user_ids(
                #     influencer.pk)
                if len(candidate_user_ids) == 0:
                    error(
                        f"0 followers for influencer {influencer.username}")
                    continue
                visited_influencer_ids.add(influencer.pk)
                record_visited_influencer_id(
                    InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto, influencer.pk)
                for candidate_user_id in candidate_user_ids:
                    if candidate_user_id not in past_dm_user_ids and candidate_user_id not in todo_dm_user_ids_from_current_session and candidate_user_id not in todo_dm_user_ids:
                        todo_dm_user_ids_from_current_session.add(
                            candidate_user_id)
                time.sleep(2)
                base_pool_size = len(todo_dm_user_ids)
                delta_pool_size = len(todo_dm_user_ids_from_current_session)
                todo_dm_user_ids.update(todo_dm_user_ids_from_current_session)
                current_pool_size = len(todo_dm_user_ids)
                set_todo_dm_user_ids(
                    InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto, todo_dm_user_ids)
                info(
                    f"users pool size (before: ${base_pool_size}) / (delta: ${delta_pool_size}) / (current: ${current_pool_size}) / (target: {dm_pool_size_target}) influencer: {influencer.username}")
        except Exception as e:
            error(
                f"Exception in getting followers for seed influencers for account {apiManager.username}: {e}")
    info(f"todo DM user pool size:{len(todo_dm_user_ids)}")


def group_dm():
    i = 0
    total_user_dm_reached = 0
    total_user_failed_to_add = 0
    todo_dm_user_ids = get_todo_dm_user_ids(
        InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto)
    todo_dm_user_ids_list = list(todo_dm_user_ids)
    ig_accounts.reverse()
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
                next_user_id = todo_dm_user_ids_list.pop()
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
        while len(todo_dm_user_ids_list) > 0 and len(users_in_this_group) < users_to_invite_per_group and consequtive_failure < 5:
            try:
                next_user_id = todo_dm_user_ids_list.pop()
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
        info(
            f"DMing from {un} to {len(users_in_this_group)} users, index: {i}")
        # try:
        #     photo_share = apiManager.client.direct_send_photo(
        #         path=crypto_poster_photo_path, thread_ids=[thread_id])
        #     info(f"DM photo share result: {photo_share}")
        # except Exception as e:
        #     error(
        #         f"Exception in DMing photo share: {e}\nusername: {un}. dm user ids: {users_in_this_group}")
        try:
            msg = apiManager.client.direct_send(
                '🔥 Crypto Currency Breaking News Updates 🔥\n🔥 BUY / SELL Signal Sharing 🔥\n\n>>> @crypto_news_pulse <<< Follow and be $RICH!!', thread_ids=[thread_id])
            info(f"DM result: {msg}")
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
        set_todo_dm_user_ids(
            InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto, set(todo_dm_user_ids_list))
        record_dm_user_ids(
            InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto, users_in_this_group)
    info(
        f"Total user DM reached: {total_user_dm_reached}, failed to add: {total_user_failed_to_add}")


if __name__ == "__main__":
    while True:
        try:
            current_start_time = datetime.datetime.now()
            hour = current_start_time.hour
            next_hour_start_time = (current_start_time + datetime.timedelta(hours=1)
                                    ).replace(minute=0, second=0, microsecond=0)
            next_hour_start_ts = next_hour_start_time.timestamp()

            maintain_todo_dm_user_pool()
            if hour % 4 == 0:
                group_dm()
            current_ts = datetime.datetime.now().timestamp()
            sec_until_next_start = max(next_hour_start_ts - current_ts, 0)
            info(f"Seconds until the next hour starts: {sec_until_next_start}")
            time.sleep(sec_until_next_start)
        except Exception as e:
            error(f"Exception in sending dm: {e}")
            time.sleep(60)
