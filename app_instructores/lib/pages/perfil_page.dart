import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart'; // Asegúrate de tener intl
import 'login_page.dart';
import 'historial_clases_page.dart'; // Importamos la nueva página de historial

// RECUERDA: Si estás en un emulador Android, usa 'http://10.0.2.2:8000'
const String baseUrl = 'http://127.0.0.1:8000';

/* ===================== PALETA DE COLORES ===================== */
class SkilandColors {
  static const Color primary = Color(0xFF1D4ED8);       // Azul Fuerte
  static const Color background = Color(0xFFF1F5F9);    // Gris Claro
  static const Color surface = Colors.white;
  static const Color textMain = Color(0xFF0F172A);      // Casi Negro
  static const Color textSecondary = Color(0xFF334155); // Gris Oscuro
  static const Color danger = Color(0xFFDC2626);        // Rojo Alerta
  static const Color dangerBg = Color(0xFFFEF2F2);      // Rojo Fondo
}

/* ===================== MODELO DE DATOS ===================== */
class InstructorProfile {
  final String rut;
  final String nombre;
  final String apellido;
  final String email;
  final String telefono;
  final String disciplina;
  final int nivel;
  final String idiomas;
  final int horasMes;
  final int alumnosMes;
  final bool activoHoy; 

  InstructorProfile({
    required this.rut,
    required this.nombre,
    required this.apellido,
    required this.email,
    required this.telefono,
    required this.disciplina,
    required this.nivel,
    required this.idiomas,
    this.horasMes = 0,
    this.alumnosMes = 0,
    this.activoHoy = false,
  });

  factory InstructorProfile.fromJson(Map<String, dynamic> json) {
    return InstructorProfile(
      rut: json['rut_usuario'] ?? '',
      nombre: json['nombre'] ?? '',
      apellido: json['apellido'] ?? '',
      email: json['correo'] ?? 'Sin correo',
      telefono: json['numero_telefono'] ?? 'Sin teléfono',
      disciplina: json['disciplina'] ?? 'General',
      nivel: (json['nivel_instructor'] as num?)?.toInt() ?? 0,
      idiomas: json['idioma'] ?? 'Español',
      
      // Keys corregidas para coincidir con Django
      horasMes: (json['total_horas'] as num?)?.toInt() ?? 0, 
      alumnosMes: (json['total_alumnos'] as num?)?.toInt() ?? 0,
      activoHoy: json['activo_hoy'] ?? false,
    );
  }
}

/* ===================== PÁGINA CON ESTADO ===================== */
class PerfilPage extends StatefulWidget {
  final String token;

  const PerfilPage({super.key, required this.token});

  @override
  State<PerfilPage> createState() => _PerfilPageState();
}

class _PerfilPageState extends State<PerfilPage> {
  bool _loading = true;
  String? _error;
  InstructorProfile? _perfil;

  @override
  void initState() {
    super.initState();
    _fetchProfile();
  }

  // --- LÓGICA DE CONEXIÓN AL BACKEND ---
  Future<void> _fetchProfile() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final url = Uri.parse('$baseUrl/api/instructor/perfil/');
      
      final resp = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
      );

      if (resp.statusCode == 200) {
        final data = jsonDecode(utf8.decode(resp.bodyBytes));
        if (mounted) {
          setState(() {
            _perfil = InstructorProfile.fromJson(data);
            _loading = false;
          });
        }
      } else {
        if (mounted) {
          setState(() {
            _error = 'Error ${resp.statusCode}: No se pudo cargar el perfil';
            _loading = false;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error de conexión. Revisa tu internet.';
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SkilandColors.background,
      appBar: AppBar(
        title: const Text(
          "Mi Perfil",
          style: TextStyle(fontWeight: FontWeight.w800, color: SkilandColors.textMain),
        ),
        centerTitle: true,
        backgroundColor: SkilandColors.surface,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: SkilandColors.textMain),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: SkilandColors.primary),
            onPressed: _fetchProfile,
          )
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(color: SkilandColors.primary),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline_rounded, size: 60, color: Colors.grey),
            const SizedBox(height: 16),
            Text(_error!, style: const TextStyle(color: SkilandColors.textSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _fetchProfile,
              style: ElevatedButton.styleFrom(backgroundColor: SkilandColors.primary),
              child: const Text("Reintentar", style: TextStyle(color: Colors.white)),
            )
          ],
        ),
      );
    }

    if (_perfil != null) {
      final p = _perfil!;
      return SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            const SizedBox(height: 10),
            
            // ===== TARJETA DE IDENTIDAD =====
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: SkilandColors.surface,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 20, offset: const Offset(0, 8)),
                ],
              ),
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: SkilandColors.primary, width: 4),
                    ),
                    child: const CircleAvatar(
                      radius: 50,
                      backgroundColor: Color(0xFFEFF6FF),
                      child: Icon(Icons.person_rounded, size: 60, color: SkilandColors.primary),
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  Text(
                    "${p.nombre} ${p.apellido}",
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: SkilandColors.textMain),
                    textAlign: TextAlign.center,
                  ),
                  
                  const SizedBox(height: 8),
                  
                  // WIDGET: BADGE DE ESTADO DE HOY
                  _buildStatusBadge(p.activoHoy),
                  const SizedBox(height: 8),

                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                    decoration: BoxDecoration(
                      color: SkilandColors.textMain,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      "${p.disciplina.toUpperCase()} • NIVEL ${p.nivel}",
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 1),
                    ),
                  ),
                  
                  const SizedBox(height: 12),
                  Text("RUT: ${p.rut}", style: const TextStyle(color: SkilandColors.textSecondary, fontWeight: FontWeight.w600)),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // ===== ESTADÍSTICAS DEL MES (Botón de Historial Mensual) =====
            Row(
              children: [
                _buildStatCard(
                  "HORAS MES", 
                  "${p.horasMes} h", 
                  Icons.timer_rounded, 
                  Colors.orange.shade700, 
                  Colors.orange.shade50,
                  onTap: () { // Navega al historial mensual detallado
                    final today = DateTime.now();
                    final startOfMonth = DateTime(today.year, today.month, 1);
                    
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => HistorialClasesPage(
                          token: widget.token,
                          fechaInicio: startOfMonth, // Filtro: Inicio del mes
                          isMonthlyDetail: true,     // Tipo: Detalle mensual
                        ),
                      ),
                    );
                  }
                ),
                const SizedBox(width: 16),
                _buildStatCard("ALUMNOS", "${p.alumnosMes}", Icons.groups_rounded, Colors.green.shade700, Colors.green.shade50),
              ],
            ),

            const SizedBox(height: 24),

            // ===== INFORMACIÓN DE CONTACTO =====
            const SizedBox(width: double.infinity, child: Text("CONTACTO & DETALLES", style: TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: SkilandColors.textSecondary, letterSpacing: 1))),
            const SizedBox(height: 12),

            _buildInfoTile(Icons.email_outlined, "Correo", p.email),
            const SizedBox(height: 12),
            _buildInfoTile(Icons.phone_outlined, "Teléfono", p.telefono),
            const SizedBox(height: 12),
            _buildInfoTile(Icons.translate_rounded, "Idiomas", p.idiomas),
            
            const SizedBox(height: 24),

            // ===== BOTÓN: HISTORIAL COMPLETO =====
            _buildHistoryButton(context, widget.token),
            // ===================================

            const SizedBox(height: 32),

            // ===== BOTÓN CERRAR SESIÓN =====
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: SkilandColors.dangerBg,
                  foregroundColor: SkilandColors.danger,
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  side: const BorderSide(color: SkilandColors.danger, width: 1.5),
                ),
                onPressed: () {
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(builder: (_) => const LoginPage()),
                    (route) => false,
                  );
                },
                icon: const Icon(Icons.logout_rounded),
                label: const Text(
                  "CERRAR SESIÓN",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                ),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      );
    }
    
    return const SizedBox();
  }
  
  // Widget para el botón de Historial Completo
  Widget _buildHistoryButton(BuildContext context, String token) {
    return Container(
      decoration: BoxDecoration(
        color: SkilandColors.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))],
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: SkilandColors.background,
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Icon(Icons.all_inclusive_rounded, color: SkilandColors.textMain, size: 24),
        ),
        title: const Text(
          "Historial Completo (Todas las Clases)",
          style: TextStyle(fontSize: 15, color: SkilandColors.textMain, fontWeight: FontWeight.w700),
        ),
        trailing: const Icon(Icons.chevron_right_rounded, color: SkilandColors.textSecondary),
        onTap: () {
          // Navega al historial sin filtros (fechaInicio = null)
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => HistorialClasesPage(token: token),
            ),
          );
        },
      ),
    );
  }

  // Widget para Tarjetas de Estadísticas (Añadido onTap)
  Widget _buildStatCard(String label, String value, IconData icon, Color color, Color bg, {VoidCallback? onTap}) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap, // Acción al tocar
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: SkilandColors.surface,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.grey.shade200),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(10)),
                child: Icon(icon, color: color, size: 24),
              ),
              const SizedBox(height: 12),
              Text(
                value,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: SkilandColors.textMain),
              ),
              Text(
                label,
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: SkilandColors.textSecondary),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // Widget para el badge de Estado
  Widget _buildStatusBadge(bool isActive) {
    final color = isActive ? Colors.green.shade700 : Colors.red.shade700;
    final bgColor = isActive ? Colors.green.shade50 : Colors.red.shade50;
    final text = isActive ? "ACTIVO HOY" : "INACTIVO HOY";

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    );
  }

  // Widget para Info Tiles
  Widget _buildInfoTile(IconData icon, String label, String value) {
    return Container(
      decoration: BoxDecoration(
        color: SkilandColors.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 5, offset: const Offset(0, 2))],
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: SkilandColors.background,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: SkilandColors.textMain, size: 20),
        ),
        title: Text(label, style: const TextStyle(fontSize: 12, color: SkilandColors.textSecondary, fontWeight: FontWeight.w600)),
        subtitle: Text(value, style: const TextStyle(fontWeight: FontWeight.w700, color: SkilandColors.textMain, fontSize: 15)),
      ),
    );
  }
}