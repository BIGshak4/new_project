/** Keep delayed auth reads from restoring a user who has already signed out. */
export function observeAuthUser<User>(
  auth: {
    getUser(): Promise<{ data: { user: User | null } }>;
    onAuthStateChange(callback: (event: string, session: { user: User } | null) => void): {
      data: { subscription: { unsubscribe(): void } };
    };
  },
  publish: (user: User | null) => void,
) {
  let live = true;
  let revision = 0;
  const { data } = auth.onAuthStateChange((_event, session) => {
    revision += 1;
    if (live) publish(session?.user ?? null);
  });
  const initialRevision = revision;
  void auth.getUser().then(
    ({ data: result }) => {
      if (live && revision === initialRevision) publish(result.user);
    },
    () => {
      if (live && revision === initialRevision) publish(null);
    },
  );
  return () => {
    live = false;
    revision += 1;
    data.subscription.unsubscribe();
  };
}

export type AccessState = {
  userId: string;
  checking: boolean;
  allowed: boolean;
  failed: boolean;
};

/** A permission result belongs to one user and one request, never a later login. */
export class AccessCheck {
  private revision = 0;

  invalidate() {
    this.revision += 1;
  }

  async run(
    userId: string,
    load: () => Promise<boolean>,
    currentUserId: () => string | null,
    publish: (state: AccessState) => void,
  ) {
    if (currentUserId() !== userId) return;
    const revision = ++this.revision;
    publish({ userId, checking: true, allowed: false, failed: false });
    let allowed = false;
    let failed = false;
    try {
      allowed = await load();
    } catch {
      failed = true;
    }
    if (revision === this.revision && currentUserId() === userId)
      publish({ userId, checking: false, allowed, failed });
  }
}

export function accessForUser(userId: string | undefined, state: AccessState | null) {
  const matching = !!userId && state?.userId === userId;
  return {
    checking: !!userId && (!matching || state.checking),
    allowed: matching && state.allowed && !state.checking,
    failed: matching && state.failed,
  };
}
