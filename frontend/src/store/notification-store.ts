import { create } from "zustand";

interface Notification {
  id: string;
  type: "success" | "error" | "info" | "warning";
  title: string;
  message?: string;
  timestamp: number;
  read: boolean;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  add: (type: Notification["type"], title: string, message?: string) => string;
  dismiss: (id: string) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  clearAll: () => void;
}

let _counter = 0;

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,

  add: (type, title, message) => {
    const id = `notif-${++_counter}`;
    set((s) => ({
      notifications: [
        { id, type, title, message, timestamp: Date.now(), read: false },
        ...s.notifications,
      ].slice(0, 50),
      unreadCount: s.unreadCount + 1,
    }));
    return id;
  },

  dismiss: (id) =>
    set((s) => {
      const n = s.notifications.find((x) => x.id === id);
      return {
        notifications: s.notifications.filter((x) => x.id !== id),
        unreadCount: s.unreadCount - (n && !n.read ? 1 : 0),
      };
    }),

  markRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((x) => (x.id === id ? { ...x, read: true } : x)),
      unreadCount: Math.max(0, s.unreadCount - 1),
    })),

  markAllRead: () =>
    set((s) => ({
      notifications: s.notifications.map((x) => ({ ...x, read: true })),
      unreadCount: 0,
    })),

  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));
