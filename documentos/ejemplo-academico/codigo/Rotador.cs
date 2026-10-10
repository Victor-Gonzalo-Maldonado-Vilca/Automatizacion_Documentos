using UnityEngine;

public class Rotador : MonoBehaviour
{
    [SerializeField] private float velocidad = 90f; // grados por segundo

    void Update()
    {
        // Independiente de los FPS gracias a Time.deltaTime
        transform.Rotate(Vector3.up, velocidad * Time.deltaTime);
    }
}
