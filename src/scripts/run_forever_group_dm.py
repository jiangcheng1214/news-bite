# load ig account from file
import requests
import datetime
import json
import os
from utils.Constants import DM_IG_ACCOUNTS
from utils.RedisClient import RedisClient

from instagram.InstagramAPIManager import (
    InstagramAPIManager,
    InstagramAPIManagerAccountType,
    get_next_dm_ig_account,
    get_past_dm_user_ids,
    get_past_visited_influencer_ids,
    get_existing_todo_dm_user_ids,
    record_dm_user_ids,
    record_visited_influencer_id,
    set_todo_dm_user_ids,
)
from utils.Logging import info, error
import time

users_to_invite_per_group = 24
CONSECUTIVE_FAILURE_THRESHOLD = 20
dm_pool_size_multiplier = 1.2
my_user_id = "545357425"
crypto_user_id = "60768462406"
fintech_user_id = "60649820282"
crypto_poster_photo_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "crypto_poster.jpg"
)
fintech_poster_photo_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "fintech_poster.jpg"
)
dm_pool_size_target = 0
all_ig_accounts = []
ig_accounts = []


def setup():
    global dm_pool_size_target, all_ig_accounts, ig_accounts
    dm_ig_accounts_str = RedisClient.shared().get(DM_IG_ACCOUNTS)
    all_ig_account_usernames = []
    if dm_ig_accounts_str:
        all_ig_accounts = json.loads(dm_ig_accounts_str)
        all_ig_account_usernames = [a[0] for a in all_ig_accounts]
    ig_accounts_file_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "credentials", "ig_acc.txt"
    )
    ig_accounts = []
    with open(ig_accounts_file_path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if len(line) > 0:
                parts = line.split("----")
                ig_accounts.append([parts[0], parts[1]])
                if (
                    all_ig_account_usernames is not None
                    and parts[0] not in all_ig_account_usernames
                ):
                    all_ig_account_usernames.append(parts[0])
                    all_ig_accounts.append([parts[0], parts[1]])
    RedisClient.shared().set(DM_IG_ACCOUNTS, json.dumps(all_ig_accounts))
    dm_pool_size_target = int(
        users_to_invite_per_group * len(ig_accounts) * dm_pool_size_multiplier
    )

    res = requests.get(
        "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100",
        headers={"Authorization": "Token 466325df764dcb62939398699aa93d167d15fbd6"},
    ).text
    list = json.loads(res)
    ips = []
    for result in list["results"]:
        ip = f"{result['proxy_address']}:{str(result['port'])}"
        ips.append(ip)
    RedisClient.shared().set("proxy_ips", json.dumps(ips))
    RedisClient.shared().set("proxy_index", 0)


def maintain_todo_dm_user_pool():
    setup()
    past_dm_user_ids = get_past_dm_user_ids(
        InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    consecitive_zero_count = 0
    todo_dm_user_ids = get_existing_todo_dm_user_ids(
        InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    info(
        f"todo DM user pool size:{len(todo_dm_user_ids)}, target: {dm_pool_size_target}"
    )
    while True:
        if consecitive_zero_count == CONSECUTIVE_FAILURE_THRESHOLD:
            break
        # visited_influencer_ids = get_past_visited_influencer_ids(
        #     InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
        # )
        todo_dm_user_ids = get_existing_todo_dm_user_ids(
            InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
        )
        if len(todo_dm_user_ids) >= dm_pool_size_target:
            break
        working_ig_account = get_next_dm_ig_account()
        un, pw = working_ig_account[0], working_ig_account[1]
        try:
            apiManager = InstagramAPIManager(
                accountType=InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther,
                username=un,
                password=pw,
            )
        except Exception as e:
            error(f"Exception in creating InstagramAPIManager for account {un}: {e}")
            consecitive_zero_count += 1
            continue
        try:
            seed_influencers = apiManager.get_non_private_influencers(
                seed_query="trading"
            )
        except Exception as e:
            error(
                f"Exception in getting seed influencers for account {apiManager.username}: {e}"
            )
            consecitive_zero_count += 1
            continue
        try:
            total_news_dm_user_count = 0
            for influencer in seed_influencers:
                todo_dm_user_ids_from_current_session = set()
                # if influencer.pk in visited_influencer_ids:
                #     continue
                should_collect_commenters = False
                candidate_user_ids = apiManager.get_follower_ids(influencer.username)
                if len(candidate_user_ids) == 0:
                    should_collect_commenters = True
                if should_collect_commenters:
                    candidate_user_ids = apiManager.get_commenter_user_ids(
                        influencer.pk
                    )
                # visited_influencer_ids.add(influencer.pk)
                # record_visited_influencer_id(
                #     InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto,
                #     influencer.pk,
                # )
                if len(candidate_user_ids) == 0:
                    error(f"0 followers for influencer {influencer.username}")
                    continue
                for candidate_user_id in candidate_user_ids:
                    if (
                        candidate_user_id not in past_dm_user_ids
                        and candidate_user_id
                        not in todo_dm_user_ids_from_current_session
                        and candidate_user_id not in todo_dm_user_ids
                    ):
                        todo_dm_user_ids_from_current_session.add(candidate_user_id)
                time.sleep(2)
                base_pool_size = len(todo_dm_user_ids)
                delta_pool_size = len(todo_dm_user_ids_from_current_session)
                total_news_dm_user_count += delta_pool_size
                todo_dm_user_ids.update(todo_dm_user_ids_from_current_session)
                current_pool_size = len(todo_dm_user_ids)
                set_todo_dm_user_ids(
                    InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto,
                    todo_dm_user_ids,
                )
                info(
                    f"users pool size (before: ${base_pool_size}) / (delta: ${delta_pool_size}) / (current: ${current_pool_size}) / (target: {dm_pool_size_target}) influencer: {influencer.username}"
                )
                if len(todo_dm_user_ids) >= dm_pool_size_target:
                    break
            if total_news_dm_user_count == 0:
                consecitive_zero_count += 1
            else:
                consecitive_zero_count = 0
        except Exception as e:
            error(
                f"Exception in getting followers for seed influencers for account {apiManager.username}: {e}"
            )
    if consecitive_zero_count == CONSECUTIVE_FAILURE_THRESHOLD:
        error(
            f"Failed to get enough users to DM in ${CONSECUTIVE_FAILURE_THRESHOLD} consecutive attempts(accounts), early return"
        )
    info(f"todo DM user pool size:{len(todo_dm_user_ids)}")


def group_dm():
    i = 0
    total_user_dm_reached = 0
    total_user_failed_to_add = 0
    todo_dm_user_ids = get_existing_todo_dm_user_ids(
        InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto
    )
    todo_dm_user_ids_list = list(todo_dm_user_ids)
    success_account = 0
    for i in range(0, len(ig_accounts)):
        if len(todo_dm_user_ids_list) == 0:
            info("No more users to DM")
            break
        account = get_next_dm_ig_account()
        un, pw = account[0], account[1]
        try:
            apiManager = InstagramAPIManager(
                accountType=InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeOther,
                username=un,
                password=pw,
            )
        except Exception as e:
            error(f"Exception in creating InstagramAPIManager for account {un}: {e}")
            continue
        thread_id = None
        for _ in range(0, 2):  # 0, 1
            try:
                next_user_id = todo_dm_user_ids_list.pop()
                dm_msg_result = apiManager.client.direct_send(
                    ".", [my_user_id, next_user_id]
                )
                thread_id = dm_msg_result.thread_id
                break
            except Exception as e:
                error(
                    f"Exception in creating thread for account {un} user_id: {next_user_id}: {e}"
                )
        if thread_id is None:
            error(f"Failed to create thread for account {un} user_id: {next_user_id}")
            continue
        users_in_this_group = [my_user_id, next_user_id]
        failed_to_add_user_count = 0
        consequtive_failure = 0
        while (
            len(todo_dm_user_ids_list) > 0
            and len(users_in_this_group) < users_to_invite_per_group
            and consequtive_failure < 10
        ):
            try:
                next_user_id = todo_dm_user_ids_list.pop()
                success = apiManager.client.add_users_to_direct_thread(
                    thread_id=thread_id, user_ids=[next_user_id]
                )
                if success:
                    users_in_this_group.append(next_user_id)
                    consequtive_failure = 0
                else:
                    failed_to_add_user_count += 1
                    consequtive_failure += 1
            except Exception as e:
                error(
                    f"Exception in adding user to group for account {un} user_id: {next_user_id}: {e}"
                )
                failed_to_add_user_count += 1
                consequtive_failure += 1
                continue
        if len(users_in_this_group) < 3:
            error(f"Failed to add enough users to group for account {un}")
        else:
            info(f"DMing from {un} to {len(users_in_this_group)} users, index: {i}")
            try:
                # msg = '🔥 Crypto Currency Breaking News Updates 🔥\n🔥 BUY / SELL Signals Sharing 🔥\n\n>>> @crypto_news_pulse <<< Follow and be $RICH!!'
                msg = "📈 Do you want to catch secrets behind Bitcoin price movements?\n💡 Do you need real-time expert BUY / SELL signals?\n🧠 Do you need to keep fresh with crypto breaking news?\n Follow and we've got you back >>> @crypto_news_pulse <<<"
                dm_msg_result = apiManager.client.direct_send(
                    msg, thread_ids=[thread_id]
                )
                info(f"DM result: {dm_msg_result}")
                info(
                    f"DMed from {un} to {len(users_in_this_group)} users, index: {i}, failed to add user count: {failed_to_add_user_count}"
                )
                total_user_dm_reached += len(users_in_this_group)
            except Exception as e:
                error(
                    f"Exception in DMing: {e}\nusername: {un}. dm user ids: {users_in_this_group}"
                )
            try:
                profile_share = apiManager.client.direct_profile_share(
                    user_id=crypto_user_id, thread_ids=[thread_id]
                )
                info(f"DM profile share result: {profile_share}")
            except Exception as e:
                error(
                    f"Exception in DMing profile share: {e}\nusername: {un}. dm user ids: {users_in_this_group}"
                )
            success_account += 1
        total_user_failed_to_add += failed_to_add_user_count
        time.sleep(5)
        set_todo_dm_user_ids(
            InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto,
            set(todo_dm_user_ids_list),
        )
        record_dm_user_ids(
            InstagramAPIManagerAccountType.InstagramAPIManagerAccountTypeCrypto,
            users_in_this_group,
        )
    info(
        f"Total user DM reached: {total_user_dm_reached}, failed to add: {total_user_failed_to_add}, success account: {success_account}, total account: {len(ig_accounts)}"
    )


if __name__ == "__main__":
    while True:
        try:
            current_start_time = datetime.datetime.now()
            hour = current_start_time.hour
            next_hour_start_time = (
                current_start_time + datetime.timedelta(hours=1)
            ).replace(minute=0, second=0, microsecond=0)
            next_hour_start_ts = next_hour_start_time.timestamp()

            maintain_todo_dm_user_pool()
            if hour % 6 == 0:  # 6 hours = 4 groups a day
                group_dm()
            current_ts = datetime.datetime.now().timestamp()
            sec_until_next_start = max(next_hour_start_ts - current_ts, 1)
            info(f"Seconds until the next hour starts: {sec_until_next_start}")
            time.sleep(sec_until_next_start)
        except Exception as e:
            error(f"Exception in sending dm: {e}")
            time.sleep(60)
