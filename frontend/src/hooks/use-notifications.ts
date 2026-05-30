"use client";

import { useNotificationStore } from "@/store/notification-store";

export function useNotifications() {
  const store = useNotificationStore();
  return {
    notifications: store.notifications,
    unreadCount: store.unreadCount,
    add: store.add,
    dismiss: store.dismiss,
    markRead: store.markRead,
    markAllRead: store.markAllRead,
    clearAll: store.clearAll,
  };
}
