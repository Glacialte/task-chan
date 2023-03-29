import discord
import openai
import datetime
import pickle
import os

# アクセストークンを設定
TASKCHAN_TOKEN = os.environ.get("TASKCHAN_TOKEN")
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Botの大元となるオブジェクトを生成する
bot: discord.Bot = discord.Bot(
    intents=discord.Intents.all(),  # 全てのインテンツを利用できるようにする
    activity=discord.Game("Reminder Bot with openai"),  # "〇〇をプレイ中"の"〇〇"を設定,
)


class Task():
    """
    タスククラス

    Attributes:
        name (str): タスク名
        description (str): タスクの説明
        due (datetime): タスクの期限
        reward (int): タスクの報酬

    Examples:
        >>> task = Task("task1", "task1の説明", datetime.datetime.now(), 100)
    """

    def __init__(self, name: str, description: str, due: datetime, reward: int) -> None:
        """[summary] タスククラス

        Args:
            name (str): タスク名
            description (str): タスクの説明
            due (datetime): タスクの期限
            reward (int): タスクの報酬

        Returns:
            None: [description]

        Examples:
            >>> task = Task("task1", "task1の説明", datetime.datetime.now(), 100)
        """
        self.name: str = name
        self.description: str = description
        self.due: datetime = due
        self.reward: int = reward


class User():
    """
    ユーザークラス

    Attributes:
        name (str): ユーザー名
        messages (list[dict[str, str]]): ユーザーのメッセージ
        point (int): ユーザーのポイント
        tasks (list[Task]): ユーザーのタスク

    Examples:
        >>> user = User("user1")
    """

    def __init__(self, name) -> None:
        self.name: str = name
        self.messages: list[dict[str, str]] = []
        self.point: int = 0
        self.tasks: list[Task] = []

    def complete_task(self, task: Task) -> None:
        self.point += task.reward
        self.tasks.remove(task)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def add_message(self, message: dict[str, str]) -> None:
        self.messages.append(message)


class TaskChan():
    server_taskchan: dict[discord.Guild, "TaskChan"] = {}
    character_settings = ''
    # サーバーとtask-chanのインスタンスを紐付けるための辞書

    def __init__(self):
        self.users: dict[discord.User, User] = {}


# 起動時に自動的に動くメソッド
@bot.event
async def on_ready():
    print("Hello! Task-chan starts working!")


# Botが見える場所でメッセージが投稿された時に動くメソッド
@bot.event
async def on_message(message: discord.Message):
    # メッセージ送信者がBot(自分を含む)だった場合は無視する
    if message.author.bot:
        return

    if not os.path.exists(f"../.gitignore/data/{message.guild.id}"):
        os.makedirs(f"../.gitignore/data/{message.guild.id}")

    if not message.content.startswith("!talk"):
        return
    
    # メッセージが!talkで始まる場合、対話する
    user_text = ''
    user_text = message.content.replace("!talk", "")
    with open('./character_settings.txt', 'r') as f:
        TaskChan.character_settings = f.read()
    messages = [
        {"role": "system", "content": TaskChan.character_settings},
        {"role": "user", "content": 'こんにちは！'},
        {"role": "assistant", "content": 'こんにちは！わたしはタスクちゃんだよ！'},
    ]
    # ユーザーの発言を追加
    if message.guild not in TaskChan.server_taskchan:
        TaskChan.server_taskchan[message.guild] = TaskChan()
    if message.author not in TaskChan.server_taskchan[message.guild].users:
        TaskChan.server_taskchan[message.guild].users[message.author] = User(message.author.name)
    user = TaskChan.server_taskchan[message.guild].users[message.author]
    if os.path.exists(f"../.gitignore/data/{message.guild.id}/{message.author.id}.pickle"):
        with open(f"../.gitignore/data/{message.guild.id}/{message.author.id}.pickle", "rb") as f:
            user = pickle.load(f)
            history = user.messages
            for h in history:
                messages.append(h)
    messages.append({"role": "user", "content": user_text})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    cont = response["choices"][0]["message"]["content"]
    # ../.gitignore/data/server_id/user_id.pickleにユーザーのデータを保存
    if os.path.exists(f"../.gitignore/data/{message.guild.id}/{message.author.id}.pickle"):
        with open(f"../.gitignore/data/{message.guild.id}/{message.author.id}.pickle", "rb") as f:
            user = pickle.load(f)
    user.add_message({"role": "user", "content": user_text})
    user.add_message({"role": "assistant", "content": cont})
    with open(f"../.gitignore/data/{message.guild.id}/{message.author.id}.pickle", "wb") as f:
        pickle.dump(user, f)
    print(cont)
    await message.channel.send(cont)

@bot.command(name="save", description="データを保存します")
async def save(ctx: discord.ApplicationContext) -> None:
    # 新しいサーバーの場合、task-chanをインスタンス化
    if ctx.guild not in TaskChan.server_taskchan:
        TaskChan.server_taskchan[ctx.guild] = TaskChan()
    if not os.path.exists(f"../.gitignore/data/{ctx.guild.id}"):
        os.makedirs(f"../.gitignore/data/{ctx.guild.id}")
    if ctx.author not in TaskChan.server_taskchan[ctx.guild].users:
        TaskChan.server_taskchan[ctx.guild].users[ctx.author] = User(ctx.author.name)
    user = TaskChan.server_taskchan[ctx.guild].users[ctx.author]
    with open(f"../.gitignore/data/{ctx.guild.id}/{ctx.author.id}.pickle", "wb") as f:
        pickle.dump(user, f)
    await ctx.respond("データを保存したよ！")


@bot.command(name="load", description="データを読み込みます")
async def load(ctx: discord.ApplicationContext):
    # 新しいサーバーの場合、task-chanをインスタンス化
    if ctx.guild not in TaskChan.server_taskchan:
        TaskChan.server_taskchan[ctx.guild] = TaskChan()
    if ctx.author not in TaskChan.server_taskchan[ctx.guild].users:
        TaskChan.server_taskchan[ctx.guild].users[ctx.author] = User(ctx.author.name)
    else:
        user = TaskChan.server_taskchan[ctx.guild].users[ctx.author]
    if not os.path.exists(f"../.gitignore/data/{ctx.guild.id}/{ctx.author.id}.pickle"):
        await ctx.respond("データがないよ！！")
    else:
        with open(f"../.gitignore/data/{ctx.guild.id}/{ctx.author.id}.pickle", "rb") as f:
            user: User = pickle.load(f)
            TaskChan.server_taskchan[ctx.guild].users[ctx.author] = user
        await ctx.respond("データ読み込み完了だよ！")


@bot.command(name="add_task", description="タスクを追加します")
async def add_task(ctx: discord.ApplicationContext, name: str, description: str, due: str, reward: int):
    print(name, description, due, reward)
    due = datetime.datetime.strptime(due, "%Y/%m/%d %H:%M")
    print(due)
    # 新しいサーバーの場合、task-chanをインスタンス化
    if ctx.guild not in TaskChan.server_taskchan:
        TaskChan.server_taskchan[ctx.guild] = TaskChan()
    # ユーザーがtask-chanのユーザーでない場合、ユーザーを追加
    if ctx.author not in TaskChan.server_taskchan[ctx.guild].users:
        TaskChan.server_taskchan[ctx.guild].users[ctx.author] = User(
            ctx.author.display_name)
    user = TaskChan.server_taskchan[ctx.guild].users[ctx.author]
    task = Task(name, description, due, reward)
    user.add_task(task)
    TaskChan.server_taskchan[ctx.guild].users[ctx.author] = user
    await ctx.respond(f"「{name}」を追加したよ！締め切りは{due.strftime('%Y/%m/%d %H:%M')}、報酬は{reward}ポイント\n頑張ってね！")


@bot.command(name="show_tasks", description="タスク一覧を表示します")
async def show_tasks(ctx: discord.ApplicationContext):
    message = ""
    # 新しいサーバーの場合、task-chanをインスタンス化
    if ctx.guild not in TaskChan.server_taskchan:
        await ctx.respond("タスクがセーブされてないよ！！")
        return
    # ユーザーがtask-chanのユーザーでない場合、ユーザーを追加
    if ctx.author not in TaskChan.server_taskchan[ctx.guild].users:
        TaskChan.server_taskchan[ctx.guild].users[ctx.author] = User(
            ctx.author.display_name)
    user = TaskChan.server_taskchan[ctx.guild].users[ctx.author]
    tasks = user.tasks
    if len(tasks) == 0:
        await ctx.respond("タスクはないみたい")
    else:
        message = "タスク一覧だよ\n"
        for task in tasks:
            message += f"・{task.name} 締め切り:{task.due.strftime('%Y/%m/%d %H:%M')} 報酬:{task.reward}ポイント\n"
            await ctx.respond(message)


@bot.command(name="show_point", description="ポイントを表示します")
async def show_point(ctx: discord.ApplicationContext):
    # 新しいサーバーの場合、task-chanをインスタンス化
    if ctx.guild not in TaskChan.server_taskchan:
        TaskChan.server_taskchan[ctx.guild] = TaskChan()
    # ユーザーがtask-chanのユーザーでない場合、ユーザーを追加
    if ctx.author not in TaskChan.server_taskchan[ctx.guild].users:
        TaskChan.server_taskchan[ctx.guild].users[ctx.author] = User(
            ctx.author.display_name)
    user = TaskChan.server_taskchan[ctx.guild].users[ctx.author]
    await ctx.respond(f"{user.name}さんのポイントは{user.point}だよ！")

# Botを起動
bot.run(TASKCHAN_TOKEN)
