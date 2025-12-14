import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
import 'login_page.dart';
import 'perfil_page.dart';
// Importamos el modelo Clase desde la página de Historial (o tu archivo models.dart)
import 'historial_clases_page.dart'; 

// RECUERDA: Si estás en un emulador Android, usa 'http://10.0.2.2:8000'
const String baseUrl = 'http://127.0.0.1:8000';

/* ===================== PALETA DE COLORES PREMIUM ===================== */
// Se usa la misma paleta en todas partes
class SkilandColors {
  static const Color background = Color(0xFFF0F4F8); 
  static const Color surface = Colors.white;
  static const Color navyDark = Color(0xFF0A2342); 
  static const Color navyMedium = Color(0xFF2D4F7C);
  static const Color textLight = Color(0xFF94A3B8); 
  static const Color primaryAccent = Color(0xFF2563EB); 
  static const Color ski = Color(0xFF00C897); 
  static const Color snow = Color(0xFF3B82F6); 
}

/* ===================== ESTILOS DE TEXTO ===================== */
class TextStyles {
  static const TextStyle dateMonth = TextStyle(
    fontSize: 26, fontWeight: FontWeight.w800, color: SkilandColors.navyDark, letterSpacing: -0.5);
  static const TextStyle dateDay = TextStyle(
    fontSize: 14, fontWeight: FontWeight.w600, color: SkilandColors.navyMedium, letterSpacing: 0.5);
    
  static const TextStyle timeStart = TextStyle(
    fontSize: 30, fontWeight: FontWeight.w900, color: SkilandColors.navyDark, height: 1.0);
  static const TextStyle timeEnd = TextStyle(
    fontSize: 14, fontWeight: FontWeight.w600, color: SkilandColors.textLight);
    
  static const TextStyle cardTitle = TextStyle(
    fontSize: 18, fontWeight: FontWeight.w800, color: SkilandColors.navyDark);
  static const TextStyle cardDetail = TextStyle(
    fontSize: 13, fontWeight: FontWeight.w700, color: SkilandColors.navyMedium);
}


/* ===================== PANTALLA PRINCIPAL (AGENDA DIARIA) ===================== */

class ClassesPage extends StatefulWidget {
  final String token;
  const ClassesPage({super.key, required this.token});

  @override
  State<ClassesPage> createState() => _ClassesPageState();
}

class _ClassesPageState extends State<ClassesPage> {
  bool _loading = false;
  String? _error;
  List<Clase> _clases = [];
  // Solo la fecha actual (sin hora)
  DateTime _selectedDate = DateTime.now().copyWith(hour: 0, minute: 0, second: 0, millisecond: 0, microsecond: 0);

  @override
  void initState() {
    super.initState();
    _fetchClases();
  }

  Future<void> _fetchClases() async {
    setState(() { _loading = true; _error = null; });
    try {
      // Pasamos solo el parámetro 'fecha' para el filtro diario
      final fecha = DateFormat('yyyy-MM-dd').format(_selectedDate);
      final url = Uri.parse('$baseUrl/api/instructor/clases/?fecha=$fecha');
      
      final resp = await http.get(
        url,
        headers: {'Authorization': 'Bearer ${widget.token}', 'Content-Type': 'application/json'},
      );

      if (resp.statusCode == 200) {
        final rawData = jsonDecode(utf8.decode(resp.bodyBytes));
        final data = rawData is Map && rawData.containsKey('results') ? rawData['results'] : rawData;

        if (data is List) {
          final clases = data.map((e) => Clase.fromJson(e)).toList();
          clases.sort((a, b) => a.horaInicio.compareTo(b.horaInicio));
          if (mounted) setState(() => _clases = clases);
        } else {
          if (mounted) setState(() => _error = 'Respuesta del servidor no válida.');
        }
      } else {
        if (mounted) setState(() => _error = 'Error ${resp.statusCode}: No se pudo actualizar la agenda.');
      }
    } catch (e) {
      if (mounted) setState(() => _error = 'Sin conexión a internet.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _cambiarDia(int delta) {
    setState(() {
      _selectedDate = _selectedDate.add(Duration(days: delta));
    });
    _fetchClases();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: SkilandColors.background,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            _buildAestheticHeader(context),
            const SizedBox(height: 10),
            _buildFloatingDateSelector(),
            const SizedBox(height: 10),
            Expanded(child: _buildContent()),
          ],
        ),
      ),
    );
  }

  // 1. HEADER (Contiene el botón de actualizar)
  Widget _buildAestheticHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Icon(Icons.landscape_rounded, color: SkilandColors.primaryAccent, size: 32),
              const SizedBox(width: 12),
              Text("SKILAND", style: TextStyle(
                fontWeight: FontWeight.w900, 
                fontSize: 18, 
                color: SkilandColors.navyDark, 
                letterSpacing: 1.5
              )),
            ],
          ),
          
          // === CONTENEDOR DE ACCIONES (Actualizar y Perfil) ===
          Row(
            children: [
              // Botón de Actualizar (Refresh)
              Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: _fetchClases, 
                  borderRadius: BorderRadius.circular(50),
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    child: Icon(Icons.refresh_rounded, color: SkilandColors.navyMedium, size: 24),
                  ),
                ),
              ),
              const SizedBox(width: 8), 

              // Botón de Perfil
              InkWell(
                onTap: () async {
                  await Navigator.push(context, MaterialPageRoute(builder: (_) => PerfilPage(token: widget.token)));
                  _fetchClases(); // Refresca la agenda al volver del perfil
                },
                borderRadius: BorderRadius.circular(50),
                child: Container(
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [BoxShadow(color: SkilandColors.primaryAccent.withOpacity(0.2), blurRadius: 12, offset: const Offset(0, 4))],
                  ),
                  child: const CircleAvatar(
                    radius: 20,
                    backgroundColor: SkilandColors.surface,
                    child: Icon(Icons.person_rounded, color: SkilandColors.primaryAccent, size: 22),
                  ),
                ),
              ),
            ],
          )
        ],
      ),
    );
  }

  // 2. SELECTOR DE FECHA
  Widget _buildFloatingDateSelector() {
    final fechaDiaMes = DateFormat('d MMM', 'es').format(_selectedDate).toUpperCase();
    final nombreDia = DateFormat('EEEE', 'es').format(_selectedDate);
    final diaCap = nombreDia[0].toUpperCase() + nombreDia.substring(1);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: SkilandColors.surface,
        borderRadius: BorderRadius.circular(30),
        boxShadow: [
          BoxShadow(color: SkilandColors.navyDark.withOpacity(0.06), blurRadius: 20, offset: const Offset(0, 8)),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildNavButton(Icons.chevron_left_rounded, () => _cambiarDia(-1)),
          Column(
            children: [
              Text(diaCap, style: TextStyles.dateDay),
              Text(fechaDiaMes, style: TextStyles.dateMonth),
            ],
          ),
          _buildNavButton(Icons.chevron_right_rounded, () => _cambiarDia(1)),
        ],
      ),
    );
  }

  Widget _buildNavButton(IconData icon, VoidCallback onTap) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(50),
        child: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: SkilandColors.background, width: 1.5)
          ),
          child: Icon(icon, color: SkilandColors.navyMedium),
        ),
      ),
    );
  }

  // 3. CONTENIDO
  Widget _buildContent() {
    if (_loading) return const Center(child: CircularProgressIndicator(color: SkilandColors.primaryAccent));
    
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.cloud_off_rounded, size: 64, color: SkilandColors.textLight.withOpacity(0.5)),
              const SizedBox(height: 16),
              Text(_error!, style: TextStyles.cardDetail, textAlign: TextAlign.center),
            ],
          ),
        ),
      );
    }

    if (_clases.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.wb_sunny_rounded, size: 80, color: Colors.amber.shade200),
            const SizedBox(height: 24),
            Text("Día Libre", style: TextStyles.dateMonth.copyWith(color: SkilandColors.navyMedium)),
            const SizedBox(height: 8),
            const Text("No hay clases programadas para hoy.", style: TextStyles.cardDetail),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 40),
      itemCount: _clases.length,
      separatorBuilder: (_, __) => const SizedBox(height: 16),
      itemBuilder: (ctx, i) => _AestheticClassCard(clase: _clases[i]),
    );
  }
}

/* ===================== CARD ESTÉTICA CON TELÉFONO ===================== */
class _AestheticClassCard extends StatelessWidget {
  final Clase clase;
  const _AestheticClassCard({required this.clase});

  @override
  Widget build(BuildContext context) {
    final horaInicio = DateFormat('HH:mm').format(clase.horaInicio);
    final horaFin = DateFormat('HH:mm').format(clase.horaFin);
    
    final bool isSki = clase.disciplina.toLowerCase() == 'ski';
    final Color accentColor = isSki ? SkilandColors.ski : SkilandColors.snow;
    final String discLabel = isSki ? "SKI" : "SNOW";

    return Container(
      decoration: BoxDecoration(
        color: SkilandColors.surface,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(color: SkilandColors.navyDark.withOpacity(0.05), blurRadius: 15, offset: const Offset(0, 6)),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: IntrinsicHeight( 
          child: Stack(
            children: [
              // Barra lateral
              Positioned(
                left: 0, top: 0, bottom: 0,
                child: Container(
                  width: 6,
                  decoration: BoxDecoration(
                    color: accentColor,
                    borderRadius: const BorderRadius.horizontal(left: Radius.circular(24)) 
                  ),
                ),
              ),
              
              Padding(
                padding: const EdgeInsets.fromLTRB(22, 20, 20, 20),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    // COLUMNA HORA
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(horaInicio, style: TextStyles.timeStart),
                        const SizedBox(height: 2),
                        Text("a $horaFin", style: TextStyles.timeEnd),
                      ],
                    ),
                    
                    // Divisor vertical
                    Container(
                      width: 1, 
                      color: SkilandColors.background, 
                      margin: const EdgeInsets.symmetric(horizontal: 20),
                      constraints: const BoxConstraints(minHeight: 60), 
                    ),
                    
                    // DETALLES
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          // Tags
                          Row(
                            children: [
                              _buildElegantTag(discLabel, accentColor),
                              const SizedBox(width: 8),
                              _buildElegantTag("NIVEL ${clase.nivel}", SkilandColors.navyMedium, outlined: true),
                            ],
                          ),
                          const SizedBox(height: 10),
                          
                          // Titular
                          Text(
                            clase.nombreTitular,
                            style: TextStyles.cardTitle,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          
                          const SizedBox(height: 8),
                          
                          // Info: Alumnos y Teléfono
                          Row(
                            children: [
                              // Pax
                              Icon(Icons.people_alt_rounded, size: 16, color: SkilandColors.navyMedium),
                              const SizedBox(width: 4),
                              Text("${clase.cantidadAlumnos}", style: TextStyles.cardDetail),
                              
                              const SizedBox(width: 16),
                              
                              // Teléfono (Solo si existe)
                              if (clase.telefono.isNotEmpty) ...[
                                Icon(Icons.phone_rounded, size: 16, color: SkilandColors.navyMedium),
                                const SizedBox(width: 4),
                                Expanded( 
                                  child: Text(
                                    clase.telefono, 
                                    style: TextStyles.cardDetail,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ]
                            ],
                          )
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildElegantTag(String text, Color color, {bool outlined = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: outlined ? Colors.transparent : color.withOpacity(0.1),
        border: Border.all(color: color.withOpacity(outlined ? 0.5 : 0), width: 1.5),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w800,
          color: color,
          letterSpacing: 0.5
        ),
      ),
    );
  }
}