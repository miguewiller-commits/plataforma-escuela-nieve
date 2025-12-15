import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart'; // 👈 1. IMPORTAR ESTO
import 'pages/login_page.dart';

import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';

// 👈 2. VARIABLE GLOBAL
// Esto te permite llamar a 'supabase.auth...' desde cualquier archivo de tu app
final supabase = Supabase.instance.client;

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 👈 3. INICIALIZAR SUPABASE
  // Pega aquí las credenciales que obtuviste en el paso anterior
  await Supabase.initialize(
    url: 'https://xpzrxbzibtcfhoowusvk.supabase.co', // Ej: https://xyz.supabase.co
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhwenJ4YnppYnRjZmhvb3d1c3ZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU3NjMwMjIsImV4cCI6MjA4MTMzOTAyMn0.fyIDB0hzEZZirv9ZOggfbPjN-YHq-aHWYvkRsgkQXOQ', // Ej: eyJhbGciOiJIUzI1NiIsInR5cCI...
  );

  // Inicializar datos locales para español (Tu código existente)
  await initializeDateFormatting('es', null);
  Intl.defaultLocale = 'es';

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'App Instructores',
      debugShowCheckedModeBanner: false,
      // Puedes agregar un tema global aquí si quieres
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const LoginPage(),
    );
  }
}