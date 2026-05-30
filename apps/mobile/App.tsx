import { StatusBar } from "expo-status-bar";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";

const API = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:3000";

type Week = { id: string; title: string };

export default function App() {
  const [weeks, setWeeks] = useState<Week[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API}/v1/weeks`)
      .then((r) => r.json())
      .then(setWeeks)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>DailyDiet Mobile</Text>
      <Text style={styles.sub}>Phase 3 scaffold — wire to {API}</Text>
      {loading && <ActivityIndicator />}
      {error ? <Text style={styles.err}>{error}</Text> : null}
      <ScrollView style={styles.list}>
        {weeks.map((w) => (
          <Text key={w.id} style={styles.item}>{w.title}</Text>
        ))}
      </ScrollView>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 48, paddingHorizontal: 16, backgroundColor: "#f6f8f4" },
  title: { fontSize: 22, fontWeight: "700", color: "#2d6a4f" },
  sub: { color: "#5a6b5a", marginBottom: 16 },
  list: { flex: 1 },
  item: { paddingVertical: 8, borderBottomWidth: 1, borderColor: "#d8e0d4" },
  err: { color: "#b00020" },
});
